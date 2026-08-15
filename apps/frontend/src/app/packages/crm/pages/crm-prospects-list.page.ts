import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Prospect, ProspectCreateRequest } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { NotificationService } from '../../../core/services/notification.service';

const PROSPECT_STATUSES = ['new', 'contacted', 'qualified', 'disqualified', 'converted'];
const PROSPECT_SOURCES = ['referral', 'web', 'event', 'outbound', 'partner', 'other'];

@Component({
  selector: 'app-crm-prospects-list-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    StatusLabelPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-prospects-list-page">
      <app-enterprise-page-header
        [title]="'crm.prospects.title' | t:lang()"
        [subtitle]="'crm.prospects.subtitle' | t:lang()"
      >
        <button type="button" class="btn btn--secondary" (click)="showCreate = !showCreate">
          {{ (showCreate ? 'common.cancel' : 'crm.prospects.create') | t:lang() }}
        </button>
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      <app-enterprise-section-card [title]="'common.filter' | t:lang()">
        <form class="form-grid">
          <app-enterprise-form-field [label]="'crm.prospects.filterStatus' | t:lang()">
            <select class="select" [(ngModel)]="statusFilter" name="statusFilter" (ngModelChange)="applyFilter()">
              <option value="">{{ 'common.all' | t:lang() }}</option>
              @for (s of statuses; track s) {
                <option [value]="s">{{ s | statusLabel }}</option>
              }
            </select>
          </app-enterprise-form-field>
        </form>

        @if (showCreate) {
          <form class="form-grid" style="margin-top: 1rem" (ngSubmit)="create()" #f="ngForm">
            <app-enterprise-form-field [label]="'common.name' | t:lang()" [required]="true">
              <input
                class="input"
                [(ngModel)]="form.display_name"
                name="display_name"
                required
                [placeholder]="'crm.prospects.namePlaceholder' | t:lang()"
              />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.prospects.company' | t:lang()">
              <input class="input" [(ngModel)]="form.company_name" name="company_name" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.email' | t:lang()">
              <input
                class="input"
                [(ngModel)]="form.email"
                name="email"
                type="email"
                [placeholder]="'crm.prospects.emailPlaceholder' | t:lang()"
              />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.prospects.phone' | t:lang()">
              <input
                class="input"
                [(ngModel)]="form.phone"
                name="phone"
                [placeholder]="'crm.prospects.phonePlaceholder' | t:lang()"
              />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.prospects.source' | t:lang()">
              <select class="select" [(ngModel)]="form.source" name="source" data-testid="crm-prospect-source">
                <option value="">{{ 'common.select' | t:lang() }}</option>
                @for (src of sources; track src) {
                  <option [value]="src">{{ ('crm.prospects.source.' + src) | t:lang() }}</option>
                }
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.notes' | t:lang()">
              <textarea class="input" [(ngModel)]="form.notes" name="notes" rows="2"></textarea>
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="!form.display_name || saving()">
                {{ (saving() ? 'common.saving' : 'common.create') | t:lang() }}
              </button>
            </div>
          </form>
        }
      </app-enterprise-section-card>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (!items().length) {
        <app-enterprise-empty-state
          [title]="'crm.prospects.empty' | t:lang()"
          [ctaLabel]="'crm.prospects.create' | t:lang()"
          (ctaClick)="showCreate = true"
        />
      } @else {
        <app-enterprise-data-table>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'common.name' | t:lang() }}</th>
                <th>{{ 'crm.prospects.company' | t:lang() }}</th>
                <th>{{ 'common.email' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th>{{ 'common.created' | t:lang() }}</th>
                <th class="muted">{{ 'common.id' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (p of items(); track p.id) {
                <tr>
                  <td>
                    <a [routerLink]="['/crm/prospects', p.id]">{{ p.display_name }}</a>
                  </td>
                  <td>{{ p.company_name || ('common.notAvailable' | t:lang()) }}</td>
                  <td>{{ p.email || ('common.notAvailable' | t:lang()) }}</td>
                  <td><app-enterprise-status-badge [status]="p.status" /></td>
                  <td class="muted">{{ p.created_at | localeDate }}</td>
                  <td class="muted">{{ p.id }}</td>
                </tr>
              }
            </tbody>
          </table>
        </app-enterprise-data-table>
        <p class="muted">{{ 'common.pageTotal' | t:{ page: page, total: total }:lang() }}</p>
        <app-enterprise-action-bar>
          <button type="button" class="btn btn--ghost" [disabled]="page <= 1" (click)="go(page - 1)">
            {{ 'common.prev' | t:lang() }}
          </button>
          <button type="button" class="btn btn--ghost" [disabled]="page * limit >= total" (click)="go(page + 1)">
            {{ 'common.next' | t:lang() }}
          </button>
        </app-enterprise-action-bar>
      }
    </div>
  `,
})
export class CrmProspectsListPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly notifications = inject(NotificationService);

  readonly statuses = PROSPECT_STATUSES;
  readonly sources = PROSPECT_SOURCES;

  statusFilter = '';
  showCreate = false;
  page = 1;
  limit = 25;
  total = 0;

  form: ProspectCreateRequest = { display_name: '' };

  readonly items = signal<Prospect[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  applyFilter(): void {
    this.page = 1;
    void this.load();
  }

  async go(p: number): Promise<void> {
    this.page = p;
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const res = await firstValueFrom(
        this.api.listProspects(this.page, this.limit, this.statusFilter || undefined),
      );
      this.items.set(res.items);
      this.total = res.total;
      this.page = res.page;
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar prospectos');
    } finally {
      this.loading.set(false);
    }
  }

  async create(): Promise<void> {
    if (!this.form.display_name || this.saving()) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.createProspect(this.form));
      this.form = { display_name: '' };
      this.showCreate = false;
      this.success.set(this.i18n.t('crm.prospects.createdMsg'));
      this.notifications.success(this.i18n.t('crm.prospects.createdMsg'));
      await this.load();
    } catch (e) {
      const msg = e instanceof CrmApiError ? e.message : 'Error al crear prospecto';
      this.error.set(msg);
      this.notifications.error(this.i18n.t('crm.prospects.create'), msg);
    } finally {
      this.saving.set(false);
    }
  }
}
