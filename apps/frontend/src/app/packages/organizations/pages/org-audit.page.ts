import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AuditEntry } from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-org-audit-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-audit-page">
      <h1>{{ 'organizations.audit.title' | t:lang() }}</h1>
      <p class="lede">
        Vista sanitizada: sin tokens, hashes ni secretos. Los JSON sensibles se resumen.
      </p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }

      @if (loading()) {
        <p class="org-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else if (!items().length) {
        <div class="org-card"><p class="org-muted">{{ 'organizations.audit.empty' | t:lang() }}.</p></div>
      } @else {
        <div class="org-card" style="overflow-x:auto">
          <table class="org-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Actor</th>
                <th>Acción</th>
                <th>Target</th>
                <th>Resultado</th>
                <th>Motivo</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              @for (e of items(); track e.id) {
                <tr>
                  <td>{{ e.occurred_at | date: 'short' }}</td>
                  <td>{{ e.actor_user_id ?? '—' }}</td>
                  <td>{{ e.action }}</td>
                  <td>{{ e.target_type }} {{ e.target_id || '' }}</td>
                  <td>{{ e.result }}</td>
                  <td>{{ e.reason || '—' }}</td>
                  <td class="org-muted">{{ summarize(e) }}</td>
                </tr>
              }
            </tbody>
          </table>
          <p class="org-muted">Página {{ page }} · total {{ total }}</p>
          <div class="org-actions">
            <button type="button" class="org-btn org-btn--ghost" [disabled]="page <= 1" (click)="go(page - 1)">Anterior</button>
            <button type="button" class="org-btn org-btn--ghost" [disabled]="page * limit >= total" (click)="go(page + 1)">Siguiente</button>
          </div>
        </div>
      }

      <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId, 'settings']">Volver</a>
    </section>
  `,
})
export class OrgAuditPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  private readonly route = inject(ActivatedRoute);

  orgId = 0;
  page = 1;
  limit = 50;
  total = 0;

  readonly items = signal<AuditEntry[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.orgId = Number(this.route.snapshot.paramMap.get('id'));
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
      const res = await firstValueFrom(this.api.listAudit(this.orgId, this.page, this.limit));
      this.items.set(res.items);
      this.total = res.total;
      this.page = res.page;
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'Error al cargar auditoría');
    } finally {
      this.loading.set(false);
    }
  }

  summarize(e: AuditEntry): string {
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
    return keys.size ? `campos: ${[...keys].slice(0, 6).join(', ')}` : '—';
  }
}
