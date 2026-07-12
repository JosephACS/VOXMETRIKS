import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CrmAuditEntry } from '../models/crm.models';

@Component({
  selector: 'app-crm-audit-page',
  standalone: true,
  imports: [CommonModule],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-audit-page">
      <h1>Auditoría CRM</h1>
      <p class="lede">
        Registro de eventos CRM y contratos. Vista sanitizada: sin tokens, hashes ni secretos.
      </p>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">Cargando…</p>
      } @else if (!items().length) {
        <div class="crm-card"><p class="crm-muted">Sin eventos de auditoría CRM.</p></div>
      } @else {
        <div class="crm-card" style="overflow-x:auto">
          <table class="crm-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Actor</th>
                <th>Fuente</th>
                <th>Acción</th>
                <th>Target</th>
                <th>Resultado</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              @for (e of items(); track e.id) {
                <tr>
                  <td class="crm-muted">{{ e.occurred_at | date:'short' }}</td>
                  <td>{{ e.actor_user_id ?? '—' }}</td>
                  <td class="crm-muted">{{ e.source }}</td>
                  <td>{{ e.action }}</td>
                  <td>{{ e.target_type }} {{ e.target_id || '' }}</td>
                  <td>
                    <span class="crm-badge"
                      [class.crm-badge--approved]="e.result === 'success'"
                      [class.crm-badge--rejected]="e.result === 'failure'">
                      {{ e.result }}
                    </span>
                  </td>
                  <td class="crm-muted">{{ summarize(e) }}</td>
                </tr>
              }
            </tbody>
          </table>
          <p class="crm-muted" style="margin-top:0.5rem">Página {{ page }} · total {{ total }}</p>
          <div class="crm-actions">
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="page <= 1" (click)="go(page - 1)">
              Anterior
            </button>
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="page * limit >= total" (click)="go(page + 1)">
              Siguiente
            </button>
          </div>
        </div>
      }
    </section>
  `,
})
export class CrmAuditPageComponent implements OnInit {
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
    return keys.size ? `campos: ${[...keys].slice(0, 5).join(', ')}` : '—';
  }
}
