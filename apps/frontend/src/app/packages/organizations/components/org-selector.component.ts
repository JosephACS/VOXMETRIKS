import { Component, HostListener, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';
import { OrganizationsApiError } from '../services/organizations-api.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-org-selector',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
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
        max-width: 220px;
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
        min-width: 240px;
        max-width: min(320px, 90vw);
        z-index: 40;
        border-radius: 10px;
        border: 1px solid var(--border, #30363d);
        background: var(--surface, #161b22);
        padding: 0.35rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      }
      .org-selector-item {
        display: block;
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
      .org-selector-item:focus-visible {
        background: color-mix(in srgb, #1ed896 12%, transparent);
        outline: none;
      }
      .org-selector-item--active {
        font-weight: 600;
      }
      .org-selector-link {
        display: block;
        padding: 0.55rem 0.65rem;
        text-decoration: none;
        color: inherit;
        border-radius: 8px;
      }
      .org-selector-link:hover {
        background: color-mix(in srgb, #1ed896 12%, transparent);
      }
      .org-selector-status {
        font-size: 0.75rem;
        opacity: 0.75;
      }
      .org-selector-error {
        color: #f97066;
        font-size: 0.8rem;
        padding: 0.35rem 0.65rem;
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
        aria-label="{{ 'organizations.selector.title' | t:lang() }}"
        (click)="toggle($event)"
      >
        <span class="org-selector-name">
          @if (ctx.isLoading()) {
            Cargando org…
          } @else if (ctx.activeOrganization(); as org) {
            {{ org.display_name }}
          } @else {
            Sin organización
          }
        </span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      @if (open()) {
        <div class="org-selector-menu" role="listbox" (click)="$event.stopPropagation()">
          @if (ctx.error()) {
            <div class="org-selector-error" role="alert">{{ ctx.error() }}</div>
          }
          @if (!ctx.organizations().length) {
            <div class="org-selector-item" role="option" aria-disabled="true">{{ 'organizations.selector.empty' | t:lang() }}</div>
          }
          @for (o of ctx.organizations(); track o.id) {
            <button
              type="button"
              class="org-selector-item"
              role="option"
              [class.org-selector-item--active]="o.id === ctx.activeOrganization()?.id"
              [attr.aria-selected]="o.id === ctx.activeOrganization()?.id"
              (click)="select(o.id, o.status)"
            >
              {{ o.display_name }}
              <div class="org-selector-status">{{ o.status }}</div>
            </button>
          }
          <a class="org-selector-link" routerLink="/organizations/new" (click)="open.set(false)">{{ 'organizations.create.title' | t:lang() }}</a>
          @if (!ctx.hasOrganization()) {
            <a class="org-selector-link" routerLink="/organizations/none" (click)="open.set(false)">Estado sin organización</a>
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

  readonly open = signal(false);
  readonly switchError = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    if (this.ctx.status() === 'idle') {
      await this.ctx.bootstrap();
    }
  }

  toggle(e: Event): void {
    e.stopPropagation();
    this.open.update((v) => !v);
    this.switchError.set(null);
  }

  @HostListener('document:click')
  close(): void {
    this.open.set(false);
  }

  async select(id: number, status: string): Promise<void> {
    this.switchError.set(null);
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
    if (id === this.ctx.activeOrganization()?.id) {
      this.open.set(false);
      return;
    }
    try {
      await this.ctx.activate(id);
      this.open.set(false);
      await this.router.navigate(['/organizations', id, 'settings']);
    } catch (e) {
      this.switchError.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo cambiar de organización');
    }
  }
}
