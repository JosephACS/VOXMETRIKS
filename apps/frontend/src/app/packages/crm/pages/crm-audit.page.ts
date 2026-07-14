import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CrmAuditEntry } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-audit-page',
  standalone: true,
  imports: [CommonModule, TranslatePipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-audit-page">
      <app-enterprise-page-header
        [title]="'crm.audit.title' | t:lang()"
        [subtitle]="'crm.audit.subtitle' | t:lang()"
      />

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="5" />
      } @else if (!items().length) {
        <app-enterprise-empty-state [title]="'crm.audit.empty' | t:lang()" />
      } @else {
        <app-enterprise-data-table>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'common.date' | t:lang() }}</th>
                <th>{{ 'common.actor' | t:lang() }}</th>
                <th>{{ 'crm.audit.source' | t:lang() }}</th>
                <th>{{ 'crm.audit.action' | t:lang() }}</th>
                <th>{{ 'crm.audit.target' | t:lang() }}</th>
                <th>{{ 'crm.audit.result' | t:lang() }}</th>
                <th>{{ 'crm.audit.detail' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (e of items(); track e.id) {
                <tr>
                  <td class="muted">{{ e.occurred_at | localeDate:true }}</td>
                  <td>{{ e.actor_user_id ?? ('common.notAvailable' | t:lang()) }}</td>
                  <td class="muted">{{ e.source }}</td>
                  <td>{{ e.action }}</td>
                  <td>{{ e.target_type }} {{ e.target_id || '' }}</td>
                  <td><app-enterprise-status-badge [status]="e.result" /></td>
                  <td class="muted">{{ summarize(e) }}</td>
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
export class CrmAuditPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);

  page = 1;
  limit = 50;
  total = 0;

  readonly items = signal<CrmAuditEntry[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async go(p: number): Promise<void> {
    this.page = p;
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const res = await firstValueFrom(this.api.listCrmAudit(this.page, this.limit));
      this.items.set(res.items);
      this.total = res.total;
      this.page = res.page;
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar auditoría CRM');
    } finally {
      this.loading.set(false);
    }
  }

  summarize(e: CrmAuditEntry): string {
    const keys = new Set<string>();
    for (const bag of [e.previous_values, e.new_values]) {
      if (!bag) continue;
      for (const k of Object.keys(bag)) {
        const lk = k.toLowerCase();
        if (lk.includes('token') || lk.includes('hash') || lk.includes('secret') || lk.includes('password')) {
          continue;
        }
        keys.add(k);
      }
    }
    return keys.size
      ? this.i18n.t('crm.audit.fieldsSummary', { fields: [...keys].slice(0, 5).join(', ') })
      : this.i18n.t('common.notAvailable');
  }
}
