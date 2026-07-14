import {
  Component,
  DestroyRef,
  ElementRef,
  HostListener,
  OnInit,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { OrganizationContextService } from '../services/organization-context.service';
import { OrganizationsApiError } from '../services/organizations-api.service';
import { OrgSelectorBridgeService } from '../services/org-selector-bridge.service';
import { Organization } from '../models/organization.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';

@Component({
  selector: 'app-org-selector',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, StatusLabelPipe],
  styles: [
    `
      .org-selector {
        position: relative;
        margin-right: 0.75rem;
      }
      .org-selector-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        max-width: 240px;
        padding: 0.35rem 0.65rem;
        border-radius: 8px;
        border: 1px solid var(--border, #30363d);
        background: transparent;
        color: inherit;
        font: inherit;
        cursor: pointer;
      }
      .org-selector-btn:focus-visible {
        outline: 2px solid #1ed896;
        outline-offset: 2px;
      }
      .org-selector-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .org-selector-menu {
        position: absolute;
        right: 0;
        top: calc(100% + 0.35rem);
        width: min(320px, 92vw);
        max-height: 320px;
        z-index: 40;
        display: flex;
        flex-direction: column;
        border-radius: 10px;
        border: 1px solid var(--border, #30363d);
        background: var(--surface, #161b22);
        padding: 0.35rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      }
      .org-selector-current {
        padding: 0.45rem 0.65rem 0.55rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 0.25rem;
      }
      .org-selector-current-label {
        display: block;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        opacity: 0.6;
        margin-bottom: 0.15rem;
      }
      .org-selector-current-name {
        font-weight: 600;
        font-size: 0.875rem;
      }
      .org-selector-search {
        width: 100%;
        box-sizing: border-box;
        margin: 0.15rem 0 0.35rem;
        padding: 0.45rem 0.65rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(0, 0, 0, 0.25);
        color: inherit;
        font: inherit;
        font-size: 0.8125rem;
      }
      .org-selector-search:focus {
        outline: 2px solid #1ed896;
        outline-offset: 1px;
      }
      .org-selector-list {
        overflow-y: auto;
        flex: 1 1 auto;
        min-height: 0;
        max-height: 200px;
        padding-right: 0.1rem;
      }
      .org-selector-item {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.15rem;
        width: 100%;
        text-align: left;
        padding: 0.55rem 0.65rem;
        border: 0;
        border-radius: 8px;
        background: transparent;
        color: inherit;
        font: inherit;
        cursor: pointer;
      }
      .org-selector-item:hover,
      .org-selector-item:focus-visible,
      .org-selector-item--focused {
        background: color-mix(in srgb, #1ed896 12%, transparent);
        outline: none;
      }
      .org-selector-item--active {
        font-weight: 600;
      }
      .org-selector-item-row {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        width: 100%;
      }
      .org-selector-item-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .org-badge {
        flex-shrink: 0;
        font-size: 0.625rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        padding: 0.12rem 0.4rem;
        border-radius: 999px;
        background: rgba(30, 216, 150, 0.18);
        color: #1ed896;
      }
      .org-selector-status {
        font-size: 0.75rem;
        opacity: 0.75;
      }
      .org-selector-link {
        display: block;
        width: 100%;
        text-align: left;
        padding: 0.55rem 0.65rem;
        text-decoration: none;
        color: inherit;
        border-radius: 8px;
        border: 0;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin-top: 0.25rem;
        background: transparent;
        font: inherit;
        cursor: pointer;
      }
      .org-selector-link:hover {
        background: color-mix(in srgb, #1ed896 12%, transparent);
      }
      .org-selector-error {
        color: #f97066;
        font-size: 0.8rem;
        padding: 0.35rem 0.65rem;
      }
      .org-selector-empty {
        padding: 0.75rem 0.65rem;
        font-size: 0.8125rem;
        opacity: 0.7;
      }
    `,
  ],
  template: `
    <div class="org-selector" data-testid="org-selector">
      <button
        type="button"
        class="org-selector-btn"
        [attr.aria-expanded]="open()"
        aria-haspopup="listbox"
        [attr.aria-label]="'organizations.selector.title' | t:lang()"
        (click)="toggle($event)"
      >
        <span class="org-selector-name">
          @if (ctx.isLoading()) {
            {{ 'organizations.selector.loading' | t:lang() }}
          } @else if (ctx.hasOrganization() && ctx.activeOrganization(); as org) {
            {{ org.display_name }}
          } @else {
            {{ 'organizations.selector.none' | t:lang() }}
          }
        </span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      @if (open()) {
        <div
          class="org-selector-menu"
          role="listbox"
          (click)="$event.stopPropagation()"
          (keydown)="onMenuKeydown($event)"
        >
          @if (ctx.hasOrganization() && ctx.activeOrganization(); as active) {
            <div class="org-selector-current">
              <span class="org-selector-current-label">{{ 'organizations.selector.current' | t:lang() }}</span>
              <div class="org-selector-current-name">{{ active.display_name }}</div>
            </div>
          }

          @if (showSearch()) {
            <input
              #searchInput
              class="org-selector-search"
              type="search"
              [placeholder]="'organizations.selector.search' | t:lang()"
              [ngModel]="query()"
              (ngModelChange)="query.set($event); focusIndex.set(0)"
              (click)="$event.stopPropagation()"
              autocomplete="off"
            />
          }

          @if (ctx.error()) {
            <div class="org-selector-error" role="alert">{{ ctx.error() }}</div>
          }

          <div class="org-selector-list">
            @if (!filteredOrgs().length) {
              <div class="org-selector-empty" role="option" aria-disabled="true">
                {{ (query() ? 'organizations.selector.notFound' : 'organizations.selector.empty') | t:lang() }}
              </div>
            } @else {
              @for (o of filteredOrgs(); track o.id; let i = $index) {
                <button
                  type="button"
                  class="org-selector-item"
                  role="option"
                  [class.org-selector-item--active]="o.id === ctx.organizationId()"
                  [class.org-selector-item--focused]="i === focusIndex()"
                  [attr.aria-selected]="o.id === ctx.organizationId()"
                  (click)="select(o)"
                  (mouseenter)="focusIndex.set(i)"
                >
                  <div class="org-selector-item-row">
                    <span class="org-selector-item-name">{{ o.display_name }}</span>
                    @if (o.is_demo) {
                      <span class="org-badge">{{ 'organizations.selector.demoBadge' | t:lang() }}</span>
                    }
                  </div>
                  <div class="org-selector-status">{{ o.status | statusLabel }}</div>
                </button>
              }
            }
          </div>

          <a class="org-selector-link" routerLink="/organizations/new" (click)="open.set(false)">
            {{ 'organizations.create.title' | t:lang() }}
          </a>
          @if (ctx.hasOrganization()) {
            <button
              type="button"
              class="org-selector-link"
              (click)="enterPersonalMode()"
            >
              {{ 'organizations.selector.noneState' | t:lang() }}
            </button>
          } @else {
            <a class="org-selector-link" routerLink="/organizations/none" (click)="open.set(false)">
              {{ 'organizations.selector.noneState' | t:lang() }}
            </a>
          }
          @if (switchError()) {
            <div class="org-selector-error" role="alert">{{ switchError() }}</div>
          }
        </div>
      }
    </div>
  `,
})
export class OrgSelectorComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  readonly ctx = inject(OrganizationContextService);
  private readonly router = inject(Router);
  private readonly bridge = inject(OrgSelectorBridgeService);
  private readonly destroyRef = inject(DestroyRef);

  readonly open = signal(false);
  readonly switchError = signal<string | null>(null);
  readonly query = signal('');
  readonly focusIndex = signal(0);

  @ViewChild('searchInput') searchInput?: ElementRef<HTMLInputElement>;

  /** Memberships already filtered by API; still key by id (never by name). */
  readonly filteredOrgs = computed(() => {
    const q = this.query().trim().toLowerCase();
    const list = this.ctx.organizations();
    if (!q) return list;
    return list.filter((o) => o.display_name.toLowerCase().includes(q) || o.slug.toLowerCase().includes(q));
  });

  readonly showSearch = computed(() => this.ctx.organizations().length > 8 || this.query().length > 0);

  async ngOnInit(): Promise<void> {
    if (this.ctx.status() === 'idle') {
      await this.ctx.bootstrap();
    }
    this.bridge.openRequests$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.open.set(true);
      this.switchError.set(null);
      this.query.set('');
      this.focusIndex.set(0);
      queueMicrotask(() => this.searchInput?.nativeElement?.focus());
    });
  }

  /** Public API for enterprise pages / bridge. */
  openMenu(): void {
    this.open.set(true);
  }

  toggle(e: Event): void {
    e.stopPropagation();
    this.open.update((v) => !v);
    this.switchError.set(null);
    if (this.open()) {
      this.query.set('');
      this.focusIndex.set(0);
      queueMicrotask(() => this.searchInput?.nativeElement?.focus());
    }
  }

  @HostListener('document:click')
  close(): void {
    this.open.set(false);
  }

  onMenuKeydown(e: KeyboardEvent): void {
    const items = this.filteredOrgs();
    if (!items.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.focusIndex.update((i) => Math.min(items.length - 1, i + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.focusIndex.update((i) => Math.max(0, i - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const org = items[this.focusIndex()];
      if (org) void this.select(org);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      this.open.set(false);
    }
  }

  async select(o: Organization): Promise<void> {
    this.switchError.set(null);
    const id = o.id;
    const status = o.status;
    if (status === 'closed') {
      this.open.set(false);
      await this.router.navigate(['/organizations/closed']);
      return;
    }
    if (status === 'suspended_by_platform') {
      this.open.set(false);
      await this.router.navigate(['/organizations/suspended']);
      return;
    }
    if (id === this.ctx.organizationId()) {
      this.open.set(false);
      await this.router.navigate(['/organizations', id, 'settings']);
      return;
    }
    try {
      await this.ctx.activate(id);
      this.open.set(false);
      await this.router.navigate(['/organizations', id, 'settings']);
    } catch (e) {
      this.switchError.set(
        e instanceof OrganizationsApiError
          ? e.message
          : this.i18n.t('organizations.selector.switchError'),
      );
    }
  }

  async enterPersonalMode(): Promise<void> {
    this.open.set(false);
    this.ctx.enterPersonalMode();
    await this.router.navigate(['/organizations/none']);
  }
}
