import { Component, inject, OnInit, OnDestroy, signal, computed, HostListener, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { LoadingService } from '../../shared/services/loading.service';
import { FavoritesService } from '../../packages/streaming/services/favorites.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { MusicPlayerService } from '../../shared/services/music-player.service';
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

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, PlayerBarComponent, NowPlayingViewComponent, TranslatePipe, OrgSelectorComponent],
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
  private player = inject(MusicPlayerService);
  private destroyRef = inject(DestroyRef);
  private platformEvents = inject(PlatformEventsService);
  private orgCtx = inject(OrganizationContextService);

  sidebarOpen = signal(false);
  sidebarCollapsed = signal(this.readCollapsedPref());
  userMenuOpen = signal(false);
  private resizeHandler = () => this.checkScreenSize();

  private static readonly COLLAPSE_KEY = 'voxmetrik_sidebar_collapsed';

  userName = computed(() => {
    this.i18n.tick();
    return this.auth.getUser()?.username ?? this.i18n.t('shell.userDefault');
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
        { path: '/artists', labelKey: 'nav.artists', icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>') },
        { path: '/tracks', labelKey: 'nav.tracks', icon: this.svgIcon('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>') },
        { path: '/genres', labelKey: 'nav.genres', icon: this.svgIcon('<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/>') },
        { path: '/audio-features', labelKey: 'nav.audioFeatures', icon: this.svgIcon('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>') },
        { path: '/search', labelKey: 'nav.search', icon: this.svgIcon('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>') },
        { path: '/playlists', labelKey: 'nav.playlists', icon: this.svgIcon('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>') },
        { path: '/liked', labelKey: 'nav.liked', icon: this.svgIcon('<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>') },
        { path: '/history', labelKey: 'nav.history', icon: this.svgIcon('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>') },
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
          path: '/organizations/none',
          labelKey: 'nav.orgStatus',
          icon: this.svgIcon('<path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M9 21v-6h6v6"/>'),
        },
        {
          path: '/organizations/new',
          labelKey: 'nav.orgCreate',
          icon: this.svgIcon('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>'),
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
      ],
    },
    {
      id: 'system',
      titleKey: 'nav.section.system',
      items: [
        { path: '/settings', labelKey: 'nav.settings', icon: this.svgIcon('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>') },
      ],
    },
  ];

  navSections = computed((): NavSection[] => {
    this.i18n.tick();
    const activeId = this.orgCtx.activeOrganization()?.id;
    return this.navConfig.map((section) => {
      if (section.id === 'organizations' && activeId) {
        return {
          id: section.id,
          title: this.i18n.t(section.titleKey),
          items: [
            {
              path: `/organizations/${activeId}/settings`,
              label: this.i18n.t('nav.orgSettings'),
              icon: section.items[0].icon,
              exact: false,
            },
            {
              path: `/organizations/${activeId}/members`,
              label: this.i18n.t('nav.orgMembers'),
              icon: this.svgIcon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
              exact: false,
            },
            {
              path: `/organizations/${activeId}/invitations`,
              label: this.i18n.t('nav.orgInvitations'),
              icon: this.svgIcon('<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>'),
              exact: false,
            },
            {
              path: `/organizations/${activeId}/audit`,
              label: this.i18n.t('nav.orgAudit'),
              icon: this.svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
              exact: false,
            },
            {
              path: '/organizations/new',
              label: this.i18n.t('nav.orgCreate'),
              icon: section.items[1].icon,
              exact: false,
            },
          ],
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
    const sections = this.navSections();
    if (this.auth.hasEngineerAccess()) return sections;
    return sections.filter((s) => s.id !== 'data');
  });

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

  constructor(public loading: LoadingService) {}

  ngOnInit() {
    this.checkScreenSize();
    window.addEventListener('resize', this.resizeHandler);
    this.history.reload();
    this.favorites.refreshIds();
    const user = this.auth.getUser();
    if (user?.preferences?.dark_mode != null) {
      this.ui.syncThemeFromDarkMode(user.preferences.dark_mode);
    }
    this.platformEvents.start(this.destroyRef);
    void this.orgCtx.bootstrap();
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
    this.player.stopPlayback();
    this.orgCtx.clearOrganizationScopedState();
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  safeSvg(svg: string): SafeHtml {
    return this.iconRender.renderSvg(svg);
  }
}
