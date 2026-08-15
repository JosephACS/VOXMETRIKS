import { Component, inject, OnInit, OnDestroy, signal, computed, HostListener, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, NavigationEnd } from '@angular/router';
import { filter, map, startWith } from 'rxjs/operators';
import { FavoritesService } from '../../packages/streaming/services/favorites.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';
import { IconRenderService } from '../../shared/services/icon-render.service';
import { PlayerBarComponent } from '../../shared/components/player-bar/player-bar.component';
import { NowPlayingViewComponent } from '../../shared/components/now-playing-view/now-playing-view.component';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { routeFadeAnimation } from '../../shared/animations/route.animations';
import { TranslationKey } from '../../core/i18n/translations';
import { PlatformEventsService } from '../../core/services/platform-events.service';
import { SafeHtml } from '@angular/platform-browser';
import { OrgSelectorComponent } from '../../packages/organizations/components/org-selector.component';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { PersonalAccountApiService } from '../../packages/personal-account/services/personal-account-api.service';
import {
  filterMainNavItems,
  filterMusicNavItems,
  filterReportingNavItems,
  filterListenerLibraryItems,
  filterListenerAccountItems,
  isProductFinalSection,
  isStaffIdentity,
  showPlatformOpsInPrimaryNav,
  showReportingSection,
  homePathForRole,
  normalizeIdentityRole,
  pathRequiresOrgHydrate,
  type NavAccessContext,
} from '../../core/navigation/nav-access.policy';
import { resolveModuleContext, type ModuleContextView } from '../../shared/navigation/module-context';
import { ModuleContextChromeComponent } from '../../shared/components/module-context-chrome.component';
import { toSignal } from '@angular/core/rxjs-interop';
import { SpaceContextService } from '../../core/spaces/space-context.service';
import { spaceNavIconMarkup } from '../../core/spaces/space-nav.icons';
import { spaceNavSectionsFor } from '../../core/spaces/space-nav.config';
import { productUserDisplayName } from '../../shared/utils/product-presentation.util';
import { SpaceSelectorComponent } from '../../shared/components/space-selector/space-selector.component';

interface NavItemConfig {
  path: string;
  labelKey: TranslationKey;
  icon: string;
  exact?: boolean;
}

interface NavSectionConfig {
  id: string;
  titleKey: TranslationKey;
  items: NavItemConfig[];
}

interface NavItem {
  path: string;
  label: string;
  icon: string;
  exact: boolean;
}

interface NavSection {
  id: string;
  title: string;
  items: NavItem[];
}

interface NavGroupConfig {
  id: string;
  titleKey: TranslationKey;
  sectionIds: string[];
}

interface NavGroupView {
  id: string;
  title: string;
  sections: NavSection[];
}

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    PlayerBarComponent,
    NowPlayingViewComponent,
    TranslatePipe,
    OrgSelectorComponent,
    SpaceSelectorComponent,
    ModuleContextChromeComponent,
  ],
  templateUrl: './dashboard-layout.component.html',
  styleUrls: ['./dashboard-layout.component.css'],
  animations: [routeFadeAnimation],
})
export class DashboardLayoutComponent implements OnInit, OnDestroy {
  readonly lang = inject(I18nService).lang;
  private auth = inject(AuthService);
  private iconRender = inject(IconRenderService);
  private i18n = inject(I18nService);
  private ui = inject(UiPreferencesService);
  router = inject(Router);
  private favorites = inject(FavoritesService);
  private history = inject(HistoryService);
  private destroyRef = inject(DestroyRef);
  private platformEvents = inject(PlatformEventsService);
  private orgCtx = inject(OrganizationContextService);
  private crmCtx = inject(CrmContextService);
  private personalApi = inject(PersonalAccountApiService);
  private spaceCtx = inject(SpaceContextService);

  sidebarOpen = signal(false);
  sidebarCollapsed = signal(this.readCollapsedPref());
  /** Spec 043 hotfix — block routed pages until org preference is restored when required. */
  orgContextHydrating = signal(false);
  orgHydrateFailed = signal(false);
  private orgHydrateTimer: ReturnType<typeof setTimeout> | null = null;

  private moduleContextUrl = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map((e) => e.urlAfterRedirects || e.url),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  /** Spec 043/054 — contextual chrome filtered by product-surface registry. */
  moduleContext = computed((): ModuleContextView | null => {
    return resolveModuleContext(this.moduleContextUrl(), this.spaceCtx.productSurfaceContext());
  });
  userMenuOpen = signal(false);
  householdOwner = signal(false);
  private resizeHandler = () => this.checkScreenSize();

  private static readonly COLLAPSE_KEY = 'voxmetrik_sidebar_collapsed';
  private static readonly NAV_GROUPS_KEY = 'voxmetrik_nav_groups_open';

  /** Spec 043 — flat role nav: ≤4 groups, no duplicate section titles. */
  private readonly navGroupConfig: NavGroupConfig[] = [
    { id: 'principal', titleKey: 'nav.group.principal', sectionIds: ['main'] },
    { id: 'library', titleKey: 'nav.group.library', sectionIds: ['music'] },
    { id: 'account', titleKey: 'nav.group.account', sectionIds: ['personalAccount'] },
    { id: 'management', titleKey: 'nav.group.management', sectionIds: ['catalogHub', 'organizations'] },
    { id: 'results', titleKey: 'nav.group.results', sectionIds: ['reporting'] },
    { id: 'data', titleKey: 'nav.group.data', sectionIds: ['data'] },
  ];

  /** Admin product groups (043). */
  private readonly adminNavGroupConfig: NavGroupConfig[] = [
    { id: 'principal', titleKey: 'nav.group.principal', sectionIds: ['main'] },
    { id: 'management', titleKey: 'nav.group.management', sectionIds: ['catalogHub', 'organizations'] },
    { id: 'results', titleKey: 'nav.group.results', sectionIds: ['reporting'] },
  ];

  /** Listener product groups (043). */
  private readonly listenerNavGroupConfig: NavGroupConfig[] = [
    { id: 'principal', titleKey: 'nav.group.principal', sectionIds: ['main'] },
    { id: 'library', titleKey: 'nav.group.library', sectionIds: ['music'] },
    { id: 'account', titleKey: 'nav.group.account', sectionIds: ['personalAccount'] },
  ];

  /** Engineer product groups (043). */
  private readonly engineerNavGroupConfig: NavGroupConfig[] = [
    { id: 'principal', titleKey: 'nav.group.principal', sectionIds: ['main'] },
    { id: 'data', titleKey: 'nav.group.data', sectionIds: ['data'] },
    { id: 'results', titleKey: 'nav.group.results', sectionIds: ['reporting'] },
  ];

  /** Reduced presentation nav for demo.business — hides technical / ops modules only in UI. */
  private readonly presentationNavGroupConfig: NavGroupConfig[] = [
    { id: 'personal', titleKey: 'nav.group.presentation.personal', sectionIds: ['main', 'personalAccount'] },
    { id: 'sales', titleKey: 'nav.group.presentation.sales', sectionIds: ['crm'] },
    { id: 'organization', titleKey: 'nav.group.presentation.organization', sectionIds: ['organizations', 'subscriptions'] },
    { id: 'collections', titleKey: 'nav.group.presentation.collections', sectionIds: ['billing'] },
    { id: 'royalties', titleKey: 'nav.group.royaltiesFinance', sectionIds: ['royalties'] },
    { id: 'results', titleKey: 'nav.group.presentation.results', sectionIds: ['businessAnalytics'] },
  ];

  /** Spec 031 — demo.artist: career, publishing, own rights & results. */
  private readonly presentationArtistNavGroupConfig: NavGroupConfig[] = [
    { id: 'career', titleKey: 'nav.group.artistCareer', sectionIds: ['artistPortal'] },
    { id: 'publishing', titleKey: 'nav.group.artistPublishing', sectionIds: ['artistPublishing'] },
    { id: 'rights', titleKey: 'nav.group.artistRightsResults', sectionIds: ['artistContracts', 'royalties'] },
    { id: 'discover', titleKey: 'nav.group.music', sectionIds: ['main'] },
  ];

  /** finance.manager — billing collections + royalties only (plus minimal listen). */
  private readonly presentationFinanceNavGroupConfig: NavGroupConfig[] = [
    { id: 'collections', titleKey: 'nav.group.collections', sectionIds: ['billing'] },
    { id: 'royalties', titleKey: 'nav.group.royaltiesFinance', sectionIds: ['royalties'] },
    { id: 'personal', titleKey: 'nav.group.presentation.personal', sectionIds: ['main', 'personalAccount'] },
  ];

  private readonly presentationAllowedPaths = new Set<string>([
    '/discover',
    '/account/subscription',
    '/account/plans',
    '/account/billing',
    '/account/household',
    '/account/profiles',
    '/crm/dashboard',
    '/crm/prospects',
    '/crm/opportunities',
    '/organizations/none',
    '/subscriptions/overview',
    '/subscriptions/plans',
    '/subscriptions/trial',
    '/billing/invoices',
    '/billing/payment-attempts',
    '/billing/reconciliation',
    '/royalties',
    '/royalties/pools',
    '/royalties/settlements',
    '/royalties/statements',
    '/payouts',
    '/business-analytics',
  ]);

  private readonly artistPortalAllowedPaths = new Set<string>([
    '/discover',
    '/artist/profile',
    '/artist/releases',
    '/artist/releases/new',
    '/artist/tracks',
    '/catalog-review',
    '/catalog-rights/contracts',
    '/catalog-rights/conflicts',
    '/royalties',
    '/royalties/statements',
    '/payouts',
  ]);

  private readonly financePresentationAllowedPaths = new Set<string>([
    '/discover',
    '/account/subscription',
    '/account/plans',
    '/account/billing',
    '/account/household',
    '/account/profiles',
    '/billing/invoices',
    '/billing/payment-attempts',
    '/billing/reconciliation',
    '/billing/refunds',
    '/billing/credit-notes',
    '/billing/manual-transfer',
    '/billing/profile',
    '/billing/ledger',
    '/royalties',
    '/royalties/pools',
    '/royalties/settlements',
    '/royalties/statements',
    '/payouts',
  ]);

  expandedNavGroups = signal<Record<string, boolean>>(this.readNavGroupsPref());

  userName = computed(() => {
    this.i18n.tick();
    const raw = this.auth.getUser()?.username ?? this.i18n.t('shell.userDefault');
    return productUserDisplayName(raw, this.i18n.t('shell.listenerDisplay'));
  });
  userPlan = computed(() => {
    this.i18n.tick();
    const plan = this.auth.getUser()?.plan ?? 'Free';
    if (plan.toLowerCase() === 'free') return this.i18n.t('shell.planFree');
    return plan;
  });
  isDemoUser = computed(() => {
    const email = this.auth.getUser()?.email ?? '';
    return email.includes('demo@') || this.userPlan().toLowerCase() === 'demo';
  });

  /** Account flagged for reduced presentation menu (demo.business). */
  isPresentationDemo = computed(() => {
    const user = this.auth.getUser();
    const username = (user?.username ?? '').toLowerCase();
    if (username === 'demo.business') return true;
    return user?.preferences?.presentation_nav === true;
  });

  /** Spec 031 artist portal mode (demo.artist / presentation_role artist). */
  isArtistPortalDemo = computed(() => {
    const user = this.auth.getUser();
    const username = (user?.username ?? '').toLowerCase();
    if (username === 'demo.artist') return true;
    const role = (user?.preferences?.presentation_role ?? '').toLowerCase();
    return role === 'artist' || role === 'artist_portal';
  });

  /** finance.manager — reduced finance-focused menu (no new permissions). */
  isFinancePresentationDemo = computed(() => {
    const user = this.auth.getUser();
    const username = (user?.username ?? '').toLowerCase();
    if (username === 'finance.manager') return true;
    const role = (user?.preferences?.presentation_role ?? '').toLowerCase();
    return role === 'finance' || role === 'finance_manager';
  });

  userRole = computed(() => (this.auth.getUser()?.role ?? 'user').toLowerCase());

  roleLabel = computed(() => {
    this.i18n.tick();
    const role = this.userRole();
    if (role === 'admin') return this.i18n.t('shell.role.admin');
    if (role === 'engineer') return this.i18n.t('shell.role.engineer');
    return this.i18n.t('shell.role.user');
  });

  isEngineerRole = computed(() => {
    const role = this.userRole();
    return role === 'admin' || role === 'engineer';
  });

  private svgIcon(path: string): string {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
  }

  private readonly navConfig: NavSectionConfig[] = [
    {
      id: 'main',
      titleKey: 'nav.section.main',
      items: [
        {
          path: '/discover',
          labelKey: 'nav.home',
          icon: this.svgIcon('<path d="M3 9.5L12 4l9 5.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V9.5z"/>'),
          exact: true,
        },
        {
          path: '/search',
          labelKey: 'nav.search',
          icon: this.svgIcon('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
        },
        {
          path: '/workpanel',
          labelKey: 'nav.workpanel',
          icon: this.svgIcon('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>'),
        },
        {
          path: '/dashboard',
          labelKey: 'nav.analyticsHub',
          icon: this.svgIcon('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
        },
        {
          path: '/insights/analytics',
          labelKey: 'nav.streamsAnalytics',
          icon: this.svgIcon('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'),
        },
        {
          path: '/insights/tracks',
          labelKey: 'nav.topTracks',
          icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
        },
      ],
    },
    {
      id: 'music',
      titleKey: 'nav.section.music',
      items: [
        { path: '/tracks', labelKey: 'nav.tracks', icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>') },
        { path: '/artists', labelKey: 'nav.artists', icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>') },
        { path: '/genres', labelKey: 'nav.genres', icon: this.svgIcon('<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/>') },
        { path: '/playlists', labelKey: 'nav.playlists', icon: this.svgIcon('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>') },
        { path: '/liked', labelKey: 'nav.liked', icon: this.svgIcon('<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>') },
        { path: '/history', labelKey: 'nav.history', icon: this.svgIcon('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>') },
        { path: '/activity', labelKey: 'nav.activity', icon: this.svgIcon('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>') },
        { path: '/audio-features', labelKey: 'nav.audioFeatures', icon: this.svgIcon('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>') },
      ],
    },
    {
      id: 'catalogHub',
      titleKey: 'nav.section.catalogHub',
      items: [
        {
          path: '/catalog',
          labelKey: 'nav.catalogHub',
          icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
        },
      ],
    },
    {
      id: 'personalAccount',
      titleKey: 'nav.section.personalAccount',
      items: [
        {
          path: '/account/subscription',
          labelKey: 'nav.personal.subscription',
          icon: this.svgIcon('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
        },
        {
          path: '/account/plans',
          labelKey: 'nav.personal.plans',
          icon: this.svgIcon('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>'),
        },
        {
          path: '/account/household',
          labelKey: 'nav.personal.household',
          icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
        },
        {
          path: '/account/billing',
          labelKey: 'nav.personal.billing',
          icon: this.svgIcon('<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>'),
        },
        {
          path: '/settings',
          labelKey: 'nav.settings',
          icon: this.svgIcon('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
        },
      ],
    },
    {
      id: 'analytics',
      titleKey: 'nav.section.analytics',
      items: [
        { path: '/analytics', labelKey: 'nav.analytics', icon: this.svgIcon('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>') },
        { path: '/trending', labelKey: 'nav.trending', icon: this.svgIcon('<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>') },
        { path: '/comparatives', labelKey: 'nav.comparatives', icon: this.svgIcon('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>') },
      ],
    },
    {
      id: 'recommendations',
      titleKey: 'nav.section.recommendations',
      items: [
        { path: '/recommendations', labelKey: 'nav.recommendations', icon: this.svgIcon('<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>') },
      ],
    },
    {
      id: 'data',
      titleKey: 'nav.section.data',
      items: [
        { path: '/elt-pipeline', labelKey: 'nav.eltPipeline', icon: this.svgIcon('<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>') },
        { path: '/explorer', labelKey: 'nav.explorer', icon: this.svgIcon('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>') },
      ],
    },
    {
      id: 'organizations',
      titleKey: 'nav.section.organizations',
      items: [
        {
          path: '/organizations/onboarding',
          labelKey: 'nav.orgOnboarding',
          icon: this.svgIcon('<path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M9 21v-6h6v6"/>'),
        },
      ],
    },
    {
      id: 'crm',
      titleKey: 'nav.section.crm',
      items: [
        {
          path: '/crm/dashboard',
          labelKey: 'nav.crm.dashboard',
          icon: this.svgIcon('<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><path d="M7 10h2l2-3 2 5 2-2h2"/>'),
        },
        {
          path: '/crm/prospects',
          labelKey: 'nav.crm.prospects',
          icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
        },
        {
          path: '/crm/contacts',
          labelKey: 'nav.crm.contacts',
          icon: this.svgIcon('<path d="M20 21v-2a4 4 0 0 0-3-3.87"/><path d="M4 21v-2a4 4 0 0 1 3-3.87"/><circle cx="12" cy="7" r="4"/>'),
        },
        {
          path: '/crm/opportunities',
          labelKey: 'nav.crm.opportunities',
          icon: this.svgIcon('<line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>'),
        },
        {
          path: '/crm/approvals',
          labelKey: 'nav.crm.approvals',
          icon: this.svgIcon('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'),
        },
        {
          path: '/crm/audit',
          labelKey: 'nav.crm.audit',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
        },
      ],
    },
    {
      id: 'subscriptions',
      titleKey: 'nav.section.subscriptions',
      items: [
        {
          path: '/subscriptions/overview',
          labelKey: 'nav.subscriptions.overview',
          icon: this.svgIcon('<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>'),
        },
        {
          path: '/subscriptions/plans',
          labelKey: 'nav.subscriptions.plans',
          icon: this.svgIcon('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'),
        },
        {
          path: '/subscriptions/trial',
          labelKey: 'nav.subscriptions.trial',
          icon: this.svgIcon('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'),
        },
      ],
    },
    {
      id: 'billing',
      titleKey: 'nav.section.billing',
      items: [
        {
          path: '/billing/invoices',
          labelKey: 'nav.billing.invoices',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>'),
        },
        {
          path: '/billing/reconciliation',
          labelKey: 'nav.billing.reconciliation',
          icon: this.svgIcon('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
        },
        {
          path: '/billing/payment-attempts',
          labelKey: 'nav.billing.paymentAttempts',
          icon: this.svgIcon('<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>'),
        },
        {
          path: '/billing/manual-transfer',
          labelKey: 'nav.billing.manualTransfer',
          icon: this.svgIcon('<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'),
        },
        {
          path: '/billing/refunds',
          labelKey: 'nav.billing.refunds',
          icon: this.svgIcon('<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>'),
        },
        {
          path: '/billing/credit-notes',
          labelKey: 'nav.billing.creditNotes',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>'),
        },
        {
          path: '/billing/profile',
          labelKey: 'nav.billing.profile',
          icon: this.svgIcon('<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>'),
        },
        {
          path: '/billing/ledger',
          labelKey: 'nav.billing.ledger',
          icon: this.svgIcon('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>'),
        },
      ],
    },
    {
      id: 'royalties',
      titleKey: 'nav.section.royalties',
      items: [
        {
          path: '/royalties',
          labelKey: 'nav.royalties.dashboard',
          icon: this.svgIcon('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
          exact: true,
        },
        {
          path: '/royalties/pools',
          labelKey: 'nav.royalties.pools',
          icon: this.svgIcon('<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'),
        },
        {
          path: '/royalties/settlements',
          labelKey: 'nav.royalties.settlements',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
        },
        {
          path: '/royalties/statements',
          labelKey: 'nav.royalties.statements',
          icon: this.svgIcon('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>'),
        },
        {
          path: '/payouts',
          labelKey: 'nav.royalties.payouts',
          icon: this.svgIcon('<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>'),
        },
      ],
    },
    {
      id: 'artistProfiles',
      titleKey: 'nav.section.artistProfiles',
      items: [
        {
          path: '/artist-profiles',
          labelKey: 'nav.artistProfiles.list',
          icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
        },
      ],
    },
    {
      id: 'artistPortal',
      titleKey: 'nav.section.distribution',
      items: [
        {
          path: '/artist/profile',
          labelKey: 'nav.artist.profile',
          icon: this.svgIcon('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
        },
        {
          path: '/artist/releases',
          labelKey: 'nav.artist.releases',
          icon: this.svgIcon('<rect x="2" y="3" width="20" height="18" rx="2"/><line x1="2" y1="9" x2="22" y2="9"/>'),
        },
        {
          path: '/artist/releases/new',
          labelKey: 'nav.artist.newRelease',
          icon: this.svgIcon('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>'),
        },
        {
          path: '/artist/tracks',
          labelKey: 'nav.artist.tracks',
          icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
        },
        {
          path: '/catalog-review',
          labelKey: 'nav.catalogReview.inbox',
          icon: this.svgIcon('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'),
        },
      ],
    },
    {
      id: 'artistPublishing',
      titleKey: 'nav.group.artistPublishing',
      items: [
        {
          path: '/catalog-review',
          labelKey: 'nav.catalogReview.inbox',
          icon: this.svgIcon('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'),
        },
        {
          path: '/artist/releases',
          labelKey: 'nav.artist.publishedReleases',
          icon: this.svgIcon('<rect x="2" y="3" width="20" height="18" rx="2"/><line x1="2" y1="9" x2="22" y2="9"/>'),
        },
      ],
    },
    {
      id: 'artistContracts',
      titleKey: 'nav.group.artistRights',
      items: [
        {
          path: '/catalog-rights/contracts',
          labelKey: 'nav.artist.contracts',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
        },
        {
          path: '/catalog-rights/conflicts',
          labelKey: 'nav.artist.relatedConflicts',
          icon: this.svgIcon('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'),
        },
      ],
    },
    {
      id: 'catalogRights',
      titleKey: 'nav.section.catalogRights',
      items: [
        {
          path: '/catalog-rights/assets',
          labelKey: 'nav.catalogRights.assets',
          icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
        },
        {
          path: '/catalog-rights/releases',
          labelKey: 'nav.catalogRights.releases',
          icon: this.svgIcon('<rect x="2" y="3" width="20" height="18" rx="2"/><line x1="2" y1="9" x2="22" y2="9"/>'),
        },
        {
          path: '/catalog-rights/contracts',
          labelKey: 'nav.catalogRights.contracts',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
        },
        {
          path: '/catalog-rights/conflicts',
          labelKey: 'nav.catalogRights.conflicts',
          icon: this.svgIcon('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'),
        },
      ],
    },
    {
      id: 'campaigns',
      titleKey: 'nav.section.campaigns',
      items: [
        {
          path: '/campaigns',
          labelKey: 'nav.campaigns.list',
          icon: this.svgIcon('<path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M14 14h7v7h-7z"/><path d="M3 14h7v7H3z"/>'),
        },
      ],
    },
    {
      id: 'businessAnalytics',
      titleKey: 'nav.section.businessAnalytics',
      items: [
        {
          path: '/business-analytics',
          labelKey: 'nav.businessAnalytics.dashboard',
          icon: this.svgIcon('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'),
        },
        {
          path: '/business-analytics/kpis',
          labelKey: 'nav.businessAnalytics.kpis',
          icon: this.svgIcon('<path d="M21 21H3V3"/><path d="M7 16l4-8 4 5 5-9"/>'),
        },
        {
          path: '/business-analytics/alerts',
          labelKey: 'nav.businessAnalytics.alerts',
          icon: this.svgIcon('<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'),
        },
      ],
    },
    {
      id: 'compliance',
      titleKey: 'nav.section.compliance',
      items: [
        {
          path: '/compliance',
          labelKey: 'nav.compliance.privacy',
          icon: this.svgIcon('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
        },
        {
          path: '/compliance/admin',
          labelKey: 'nav.compliance.admin',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>'),
        },
      ],
    },
    {
      id: 'reporting',
      titleKey: 'nav.section.reporting',
      items: [
        {
          path: '/reports',
          labelKey: 'nav.reporting.reports',
          icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>'),
        },
        {
          path: '/simple-reports',
          labelKey: 'nav.reporting.simpleReports',
          icon: this.svgIcon('<path d="M3 3h18v4H3zM3 10h18v4H3zM3 17h18v4H3z"/>'),
        },
        {
          path: '/complex-reports',
          labelKey: 'nav.reporting.complexReports',
          icon: this.svgIcon('<path d="M3 3v18h18"/><path d="M7 16l4-8 4 5 5-9"/>'),
        },
        {
          path: '/business-decisions',
          labelKey: 'nav.reporting.decisions',
          icon: this.svgIcon('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'),
        },
      ],
    },
    {
      id: 'customerSuccess',
      titleKey: 'nav.section.customerSuccess',
      items: [
        {
          path: '/customer-success',
          labelKey: 'nav.customerSuccess.dashboard',
          icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'),
        },
        {
          path: '/support',
          labelKey: 'nav.customerSuccess.support',
          icon: this.svgIcon('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'),
        },
      ],
    },
    {
      id: 'platformOps',
      titleKey: 'nav.section.platformOps',
      items: [
        {
          path: '/platform-ops',
          labelKey: 'nav.platformOps.dashboard',
          icon: this.svgIcon('<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'),
        },
        {
          path: '/platform-ops/audio-unresolved',
          labelKey: 'nav.platformOps.audioUnresolved',
          icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
        },
      ],
    },
  ];

  navSections = computed((): NavSection[] => {
    this.i18n.tick();
    const activeId = this.orgCtx.activeOrganization()?.id;
    const tier = this.orgCtx.accessTier();
    return this.navConfig.map((section) => {
      if (section.id === 'organizations' && activeId) {
        const items: NavSection['items'] = [
          {
            path: `/organizations/${activeId}`,
            label: this.i18n.t('nav.organizationHub'),
            icon: section.items[0].icon,
            exact: false,
          },
        ];
        if (tier === 'onboarding') {
          items.push({
            path: '/organizations/onboarding',
            label: this.i18n.t('nav.orgOnboarding'),
            icon: section.items[0].icon,
            exact: false,
          });
        }
        return {
          id: section.id,
          title: this.i18n.t(section.titleKey),
          items,
        };
      }
      return {
        id: section.id,
        title: this.i18n.t(section.titleKey),
        items: section.items.map((item) => ({
          path: item.path,
          label: this.i18n.t(item.labelKey),
          icon: item.icon,
          exact: item.exact ?? false,
        })),
      };
    });
  });

  visibleNavSections = computed(() => {
    // Tick permission/CRM/subscription signals so nav updates after bootstrap.
    this.orgCtx.permissions();
    this.orgCtx.hasOrganization();
    this.orgCtx.organizationSubscription();
    this.orgCtx.accessTier();
    this.crmCtx.hasCrmAccess();
    this.crmCtx.permissions();
    this.isPresentationDemo();
    this.isArtistPortalDemo();
    this.isFinancePresentationDemo();
    this.householdOwner();

    const sections = this.navSections();
    const engineer = this.auth.hasEngineerAccess();
    const hasOrg = this.orgCtx.hasOrganization();
    const orgPerm = (code: string) => this.orgCtx.hasPermission(code);
    const canOrg = (
      kind: 'onboarding' | 'recovery' | 'operational' | 'org_admin_basic' | 'org_admin_advanced',
      perm?: string,
    ) => this.orgCtx.canAccessModule(kind, perm ?? null);
    const presentation = this.isPresentationDemo();
    const artistPortal = this.isArtistPortalDemo();
    const financeNav = this.isFinancePresentationDemo();
    const platformAdminRole = this.crmCtx.roles().includes('platform_admin');
    const platformAdmin = engineer || platformAdminRole;
    const navCtx: NavAccessContext = {
      identityRole: this.userRole(),
      platformAdmin: platformAdminRole,
      presentationMode: presentation || artistPortal || financeNav,
    };

    if (artistPortal) {
      const filtered = sections.filter(
        (s) =>
          s.id === 'artistPortal' ||
          s.id === 'artistPublishing' ||
          s.id === 'artistContracts' ||
          s.id === 'royalties' ||
          s.id === 'main',
      );
      return filtered
        .map((s) => {
          let items = s.items.filter((item) =>
            this.isArtistPortalPathAllowed(item.path, s.id),
          );
          if (s.id === 'artistPortal') {
            items = items.filter((item) => item.path !== '/catalog-review');
          }
          if (s.id === 'artistPublishing') {
            const canReview = orgPerm('publishing.review');
            items = items.filter((item) => {
              if (item.path === '/catalog-review') return canReview;
              return true;
            });
          }
          if (s.id === 'artistContracts') {
            const canContracts =
              orgPerm('catalog.view') ||
              orgPerm('rights.view') ||
              orgPerm('contract.view') ||
              orgPerm('publishing.view') ||
              (hasOrg && canOrg('operational'));
            if (!canContracts) items = [];
          }
          if (s.id === 'royalties' && !canOrg('operational')) {
            items = [];
          }
          return { ...s, items };
        })
        .filter((s) => s.items.length > 0);
    }

    if (financeNav) {
      const filtered = sections.filter(
        (s) =>
          s.id === 'main' ||
          s.id === 'personalAccount' ||
          s.id === 'billing' ||
          s.id === 'royalties',
      );
      return filtered
        .map((s) => {
          let items = s.items.filter((item) => this.isFinancePresentationPathAllowed(item.path, s.id));
          if (s.id === 'main') {
            items = items.filter((item) => item.path === '/discover');
          }
          if (s.id === 'billing' && !canOrg('recovery')) items = [];
          if (s.id === 'royalties' && !canOrg('operational')) items = [];
          return { ...s, items };
        })
        .filter((s) => s.items.length > 0);
    }

    const filtered = sections.filter((s) => {
      if (presentation) {
        return (
          s.id === 'main' ||
          s.id === 'personalAccount' ||
          s.id === 'crm' ||
          s.id === 'organizations' ||
          s.id === 'subscriptions' ||
          s.id === 'billing' ||
          s.id === 'royalties' ||
          s.id === 'businessAnalytics'
        );
      }
      // Spec 038 — product-final shell: drop demo sections from normal product nav.
      if (!isProductFinalSection(s.id, navCtx)) {
        return false;
      }
      const role = (navCtx.identityRole || 'user').toLowerCase();
      // Spec 043 — role shells
      if (role === 'admin') {
        if (s.id === 'main' || s.id === 'reporting') return true;
        if (s.id === 'catalogHub') {
          return hasOrg && canOrg('operational');
        }
        if (s.id === 'organizations') {
          return hasOrg && canOrg('org_admin_basic', 'organization.view');
        }
        return false;
      }
      if (role === 'engineer') {
        if (s.id === 'main' || s.id === 'data' || s.id === 'reporting') return true;
        return false;
      }
      // Listener / default user
      if (s.id === 'main' || s.id === 'music' || s.id === 'personalAccount') return true;
      return false;
    });

    const withItemFilters = filtered.map((s) => {
      let items = s.items;
      const role = (navCtx.identityRole || 'user').toLowerCase();
      if (s.id === 'main') {
        items = filterMainNavItems(items, navCtx);
      }
      if (s.id === 'music') {
        if (role === 'user' || (!isStaffIdentity(navCtx.identityRole) && !navCtx.platformAdmin)) {
          items = filterListenerLibraryItems(filterMusicNavItems(items, navCtx));
        } else {
          items = filterMusicNavItems(items, navCtx);
        }
      }
      if (s.id === 'reporting') {
        items = filterReportingNavItems(items, navCtx);
      }
      if (s.id === 'data' && role === 'engineer') {
        // Ingeniería de datos + explorador (Estado técnico is /workpanel in Principal / space nav).
        items = items.filter((item) => item.path.split('?')[0] === '/explorer' || item.path.split('?')[0] === '/elt-pipeline');
      }
      if (s.id === 'personalAccount') {
        if (role === 'user' || !isStaffIdentity(navCtx.identityRole)) {
          items = filterListenerAccountItems(items);
        } else {
          items = items.filter((item) => {
            if (item.path === '/account/household') return this.householdOwner();
            return true;
          });
        }
      }
      if (s.id === 'platformOps' && !showPlatformOpsInPrimaryNav(navCtx)) {
        items = [];
      }
      if (s.id === 'artistPortal') {
        items = items.filter((item) => {
          if (item.path === '/catalog-review') {
            return orgPerm('publishing.review');
          }
          return true;
        });
      }
      if (s.id === 'subscriptions' && this.orgCtx.accessTier() === 'onboarding') {
        items = items.filter(
          (item) =>
            item.path === '/subscriptions/plans' ||
            item.path === '/subscriptions/trial' ||
            item.path === '/subscriptions/select-plan' ||
            item.path === '/subscriptions/overview',
        );
      }
      return { ...s, items };
    });

    if (!presentation) return withItemFilters.filter((s) => s.items.length > 0);

    return withItemFilters
      .map((s) => {
        let items = s.items.filter((item) => this.isPresentationPathAllowed(item.path, s.id));
        if (s.id === 'organizations' && !canOrg('org_admin_basic')) items = [];
        if (s.id === 'subscriptions' && !canOrg('onboarding')) items = [];
        if (s.id === 'billing' && !canOrg('recovery')) items = [];
        if (s.id === 'royalties' && !canOrg('operational')) items = [];
        if (s.id === 'businessAnalytics' && !canOrg('operational')) items = [];
        return { ...s, items };
      })
      .filter((s) => s.items.length > 0);
  });

  private isArtistPortalPathAllowed(path: string, sectionId: string): boolean {
    if (this.artistPortalAllowedPaths.has(path)) return true;
    if (sectionId === 'main') return path === '/discover';
    if (sectionId === 'royalties') {
      return path === '/royalties' || path === '/royalties/statements' || path === '/payouts';
    }
    if (sectionId === 'artistContracts') {
      return path === '/catalog-rights/contracts' || path === '/catalog-rights/conflicts';
    }
    if (sectionId === 'artistPublishing') {
      return path === '/catalog-review' || path === '/artist/releases';
    }
    if (sectionId === 'artistPortal') {
      return (
        path === '/artist/profile' ||
        path === '/artist/releases' ||
        path === '/artist/releases/new' ||
        path === '/artist/tracks'
      );
    }
    return false;
  }

  private isPresentationPathAllowed(path: string, sectionId: string): boolean {
    if (this.presentationAllowedPaths.has(path)) return true;
    if (sectionId === 'organizations') {
      // Active org: only settings as “organization status”
      return /\/organizations\/\d+\/settings$/.test(path) || path === '/organizations/none';
    }
    if (sectionId === 'main') return path === '/discover';
    if (sectionId === 'personalAccount') {
      return (
        path === '/account/subscription' ||
        path === '/account/plans' ||
        path === '/account/billing' ||
        path === '/account/household' ||
        path === '/account/profiles'
      );
    }
    if (sectionId === 'crm') {
      return (
        path === '/crm/dashboard' ||
        path === '/crm/prospects' ||
        path === '/crm/opportunities'
      );
    }
    if (sectionId === 'subscriptions') {
      return (
        path === '/subscriptions/overview' ||
        path === '/subscriptions/plans' ||
        path === '/subscriptions/trial'
      );
    }
    if (sectionId === 'billing') {
      return (
        path === '/billing/invoices' ||
        path === '/billing/payment-attempts' ||
        path === '/billing/reconciliation'
      );
    }
    if (sectionId === 'royalties') {
      return (
        path === '/royalties' ||
        path === '/royalties/pools' ||
        path === '/royalties/settlements' ||
        path === '/royalties/statements' ||
        path === '/payouts'
      );
    }
    if (sectionId === 'businessAnalytics') {
      return path === '/business-analytics';
    }
    return false;
  }

  private isFinancePresentationPathAllowed(path: string, sectionId: string): boolean {
    if (this.financePresentationAllowedPaths.has(path)) return true;
    if (sectionId === 'main') return path === '/discover';
    if (sectionId === 'personalAccount') {
      return (
        path === '/account/subscription' ||
        path === '/account/plans' ||
        path === '/account/billing' ||
        path === '/account/household' ||
        path === '/account/profiles'
      );
    }
    if (sectionId === 'billing') {
      return path.startsWith('/billing/');
    }
    if (sectionId === 'royalties') {
      return (
        path === '/royalties' ||
        path === '/royalties/pools' ||
        path === '/royalties/settlements' ||
        path === '/royalties/statements' ||
        path === '/payouts'
      );
    }
    return false;
  }

  visibleNavGroups = computed((): NavGroupView[] => {
    this.i18n.tick();
    // Spec 054 — single space-nav authority (no presentation / username shell bypass).
    const active = this.spaceCtx.activeSpace();
    if (this.spaceCtx.status() === 'ready' && active) {
      return this.buildSpaceNavGroups();
    }
    const predicted = this.predictSpaceNavKind();
    if (predicted) {
      const access = {
        ...this.spaceCtx.productSurfaceContext(),
        ready: false,
        activeSpace: predicted.kind,
        organizationId: predicted.organizationId ?? undefined,
      };
      return this.buildSpaceNavGroupsFromSections(
        spaceNavSectionsFor(predicted.kind, {
          organizationId: predicted.organizationId,
          access,
        }),
      );
    }
    // Stable empty shell while identity is unknown — never flash privileged links.
    return [];
  });

  /** Predict space kind for stable sidebar before bootstrap completes. */
  private predictSpaceNavKind(): {
    kind: 'personal' | 'organization' | 'data_ops' | 'platform_admin';
    organizationId: number | null;
  } | null {
    const role = normalizeIdentityRole(this.userRole());
    if (role === 'engineer') {
      return { kind: 'data_ops', organizationId: null };
    }
    if (role === 'admin') {
      const orgId =
        this.orgCtx.organizationId() ?? this.orgCtx.organizations()[0]?.id ?? null;
      if (orgId != null) return { kind: 'organization', organizationId: orgId };
      return { kind: 'platform_admin', organizationId: null };
    }
    if (role === 'user') {
      return { kind: 'personal', organizationId: null };
    }
    return null;
  }

  /** Spec 045 — map SpaceNavSection[] into shell NavGroupView. */
  private buildSpaceNavGroups(): NavGroupView[] {
    return this.buildSpaceNavGroupsFromSections(this.spaceCtx.navSections());
  }

  private buildSpaceNavGroupsFromSections(
    sections: ReturnType<typeof spaceNavSectionsFor>,
  ): NavGroupView[] {
    return sections.map((section) => ({
      id: section.id,
      title: this.i18n.t(section.titleKey),
      sections: [
        {
          id: section.id,
          title: this.i18n.t(section.titleKey),
          items: section.items.map((item) => {
            const label = this.i18n.t(item.labelKey);
            return {
              path: item.path,
              label,
              icon: this.svgIcon(spaceNavIconMarkup(item.iconId)),
              exact: item.exact ?? false,
            };
          }),
        },
      ],
    }));
  }

  userInitial = computed(() => this.userName().charAt(0).toUpperCase());
  avatarGradient = computed(() => {
    const id = this.auth.getUser()?.id ?? 0;
    const gradients = [
      'linear-gradient(135deg, #1ed896, #148f5e)',
      'linear-gradient(135deg, #3b82f6, #1e3a8a)',
      'linear-gradient(135deg, #a855f7, #6b21a8)',
    ];
    return gradients[id % gradients.length];
  });

  ngOnInit() {
    this.checkScreenSize();
    window.addEventListener('resize', this.resizeHandler);
    this.history.reload();
    this.favorites.refreshIds();
    // Staff: keep Principal + technical admin groups open so engineering tools are discoverable.
    if (this.auth.hasEngineerAccess()) {
      this.expandedNavGroups.update((prev) => ({
        ...prev,
        principal: true,
        results: true,
        admin: true,
      }));
    }
    const user = this.auth.getUser();
    if (user?.preferences?.dark_mode != null) {
      this.ui.syncThemeFromDarkMode(user.preferences.dark_mode);
    }
    this.platformEvents.start(this.destroyRef);
    // Spec 045 — spaces bootstrap; org hydrate gate only where org context is required.
    if (pathRequiresOrgHydrate(this.router.url, this.auth.role())) {
      this.startOrgHydrate();
    } else {
      this.orgContextHydrating.set(false);
      void this.spaceCtx.bootstrap().catch(() => undefined);
    }
    this.ensureActiveNavGroupOpen();
    this.refreshHouseholdRole();
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((e) => {
        this.ensureActiveNavGroupOpen();
        void this.spaceCtx.ensureSpaceMatchesRoute(e.urlAfterRedirects || e.url);
        // Entering an org-scoped route after a personal surface: restore if needed.
        if (
          pathRequiresOrgHydrate(e.urlAfterRedirects || e.url, this.auth.role()) &&
          this.spaceCtx.status() !== 'ready' &&
          !this.orgContextHydrating()
        ) {
          this.startOrgHydrate();
        }
      });
  }

  private startOrgHydrate(): void {
    this.orgHydrateFailed.set(false);
    this.orgContextHydrating.set(true);
    if (this.orgHydrateTimer != null) clearTimeout(this.orgHydrateTimer);
    this.orgHydrateTimer = setTimeout(() => {
      if (this.orgContextHydrating()) {
        this.orgHydrateFailed.set(true);
        this.orgContextHydrating.set(false);
      }
    }, 12_000);
    void this.spaceCtx
      .bootstrap()
      .then(() => {
        this.orgHydrateFailed.set(false);
      })
      .catch(() => {
        this.orgHydrateFailed.set(true);
      })
      .finally(() => {
        if (this.orgHydrateTimer != null) {
          clearTimeout(this.orgHydrateTimer);
          this.orgHydrateTimer = null;
        }
        this.orgContextHydrating.set(false);
        this.ensureActiveNavGroupOpen();
      });
  }

  retryOrgHydrate(): void {
    this.startOrgHydrate();
  }

  roleHomePath(): string {
    return homePathForRole(this.auth.role());
  }

  canManageHousehold(): boolean {
    return this.householdOwner();
  }

  /** Active membership — hide “VOXMETRIKS para empresas” once the user already has an org context. */
  hasBusinessOrganization(): boolean {
    return this.orgCtx.hasOrganization();
  }

  /**
   * Classic org switcher — hidden when the space selector is active (045).
   * Fallback only while spaces are not ready yet.
   */
  showOrgSelector(): boolean {
    if (this.spaceCtx.status() === 'ready') return false;
    return this.orgCtx.organizations().length > 0 || this.orgCtx.hasOrganization();
  }

  /** Spec 045 — prominent only when more than one product space exists. */
  showSpaceSelector(): boolean {
    return this.spaceCtx.showSpaceSelector();
  }

  private refreshHouseholdRole(): void {
    this.personalApi.getHousehold().subscribe({
      next: (h) => {
        const role = (h as { my_role?: string })?.my_role;
        this.householdOwner.set(role === 'owner');
      },
      error: () => this.householdOwner.set(false),
    });
  }

  isNavGroupOpen(groupId: string): boolean {
    if (this.sidebarCollapsed()) return true;
    const state = this.expandedNavGroups();
    if (state[groupId] != null) return state[groupId];
    // Compact product nav (classic + space ids) stays open; only the old demo "admin" pack stays closed.
    if (groupId === 'admin') return false;
    return true;
  }

  toggleNavGroup(groupId: string, event?: Event): void {
    event?.stopPropagation();
    if (this.sidebarCollapsed()) return;
    this.expandedNavGroups.update((prev) => {
      const next = { ...prev, [groupId]: !this.isNavGroupOpen(groupId) };
      this.persistNavGroupsPref(next);
      return next;
    });
  }

  private ensureActiveNavGroupOpen(): void {
    const url = this.router.url.split('?')[0];
    for (const group of this.visibleNavGroups()) {
      const hit = group.sections.some((section) =>
        section.items.some((item) =>
          item.exact ? url === item.path : url === item.path || url.startsWith(`${item.path}/`),
        ),
      );
      if (hit) {
        this.expandedNavGroups.update((prev) => {
          if (prev[group.id]) return prev;
          const next = { ...prev, [group.id]: true };
          this.persistNavGroupsPref(next);
          return next;
        });
        break;
      }
    }
  }

  private readNavGroupsPref(): Record<string, boolean> {
    try {
      const raw = localStorage.getItem(DashboardLayoutComponent.NAV_GROUPS_KEY);
      if (!raw) {
        return {
          principal: true,
          library: true,
          account: true,
          management: true,
          results: true,
          data: true,
          music: true,
          admin: false,
          'space-main': true,
          'space-library': true,
          'space-account': true,
          'space-org-main': true,
          'space-org-plan': true,
          'space-org-crm': true,
          'space-org-growth': true,
          'space-org-rights': true,
          'space-org-cs': true,
          'space-data': true,
          'space-platform': true,
          'space-artist': true,
        };
      }
      const parsed = JSON.parse(raw) as Record<string, boolean>;
      return {
        principal: true,
        library: true,
        account: true,
        management: true,
        results: true,
        data: true,
        music: true,
        admin: false,
        'space-main': true,
        'space-library': true,
        'space-account': true,
        'space-org-main': true,
        'space-org-plan': true,
        'space-org-crm': true,
        'space-org-growth': true,
        'space-org-rights': true,
        'space-org-cs': true,
        'space-data': true,
        'space-platform': true,
        'space-artist': true,
        ...parsed,
      };
    } catch {
      return {
        principal: true,
        library: true,
        account: true,
        management: true,
        results: true,
        data: true,
        music: true,
        admin: false,
        'space-main': true,
        'space-library': true,
        'space-account': true,
        'space-org-main': true,
        'space-org-plan': true,
        'space-org-crm': true,
        'space-org-growth': true,
        'space-org-rights': true,
        'space-org-cs': true,
        'space-data': true,
        'space-platform': true,
        'space-artist': true,
      };
    }
  }

  private persistNavGroupsPref(state: Record<string, boolean>): void {
    try {
      localStorage.setItem(DashboardLayoutComponent.NAV_GROUPS_KEY, JSON.stringify(state));
    } catch {
      /* ignore */
    }
  }

  ngOnDestroy() {
    window.removeEventListener('resize', this.resizeHandler);
  }

  @HostListener('document:click')
  closeUserMenuOnOutsideClick() {
    this.userMenuOpen.set(false);
  }

  toggleSidebar() {
    this.sidebarOpen.update((v) => !v);
  }

  toggleSidebarCollapse() {
    this.sidebarCollapsed.update((v) => {
      const next = !v;
      localStorage.setItem(DashboardLayoutComponent.COLLAPSE_KEY, String(next));
      return next;
    });
  }

  closeSidebar() {
    if (window.innerWidth >= 1024) return;
    this.sidebarOpen.set(false);
  }

  private readCollapsedPref(): boolean {
    try {
      return localStorage.getItem(DashboardLayoutComponent.COLLAPSE_KEY) === 'true';
    } catch {
      return false;
    }
  }

  isDarkTheme = computed(() => this.ui.isVisuallyDark());

  themeToggleAria = computed(() =>
    this.isDarkTheme()
      ? this.i18n.t('shell.theme.toLight')
      : this.i18n.t('shell.theme.toDark'),
  );

  toggleTheme(): void {
    this.ui.toggleDarkLight();
    this.auth.persistDarkMode(this.ui.isVisuallyDark());
  }

  toggleUserMenu(e: Event) {
    e.stopPropagation();
    this.userMenuOpen.update((v) => !v);
  }

  checkScreenSize() {
    if (window.innerWidth >= 1024) {
      this.sidebarOpen.set(true);
    } else {
      this.sidebarOpen.set(false);
    }
  }

  logout() {
    // Cleanup lives in SessionCleanupCoordinator (invoked by AuthService.logout)
    // so the logout and 401 paths can never drift apart.
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  safeSvg(svg: string): SafeHtml {
    return this.iconRender.renderSvg(svg);
  }
}
