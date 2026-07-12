import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { ApprovalRequest } from '../models/crm.models';

@Component({
  selector: 'app-crm-approvals-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-approvals-page">
      <h1>Aprobaciones pendientes</h1>
      <p class="lede">Solicitudes de aprobación de descuento sobre cotizaciones.</p>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">Cargando…</p>
      } @else if (!items().length) {
        <div class="crm-card"><p class="crm-muted">No hay solicitudes de aprobación pendientes.</p></div>
      } @else {
        <div class="crm-card" style="overflow-x:auto">
          <table class="crm-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Tipo</th>
                <th>Objeto</th>
                <th>Motivo</th>
                <th>Umbral</th>
                <th>Estado</th>
                <th>Solicitado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (a of items(); track a.id) {
                <tr>
                  <td>{{ a.id }}</td>
                  <td>{{ a.object_type }}</td>
                  <td>#{{ a.object_id }}</td>
                  <td>{{ a.reason || '—' }}</td>
                  <td>{{ a.threshold_ref != null ? (a.threshold_ref | number:'1.0-2') + '%' : '—' }}</td>
                  <td><span class="crm-badge crm-badge--{{ a.status }}">{{ a.status }}</span></td>
                  <td class="crm-muted">{{ a.requested_at | date:'short' }}</td>
                  <td>
                    @if (a.status === 'pending') {
                      <div style="display:flex;gap:0.4rem;flex-wrap:wrap">
                        <button type="button" class="crm-btn" style="padding:0.3rem 0.6rem;font-size:0.8rem"
                          [disabled]="saving()"
                          (click)="review(a.id, 'approve')">
                          Aprobar
                        </button>
                        <button type="button" class="crm-btn crm-btn--danger" style="padding:0.3rem 0.6rem;font-size:0.8rem"
                          [disabled]="saving()"
                          (click)="review(a.id, 'reject')">
                          Rechazar
                        </button>
                      </div>
                    } @else {
                      <span class="crm-muted">{{ a.reviewed_at | date:'shortDate' }}</span>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
          <p class="crm-muted" style="margin-top:0.5rem">Página {{ page }} · total {{ total }}</p>
          <div class="crm-actions">
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="page <= 1" (click)="go(page - 1)">Anterior</button>
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="page * limit >= total" (click)="go(page + 1)">Siguiente</button>
          </div>
        </div>
      }
    </section>
  `,
})
export class CrmApprovalsPageComponent implements OnInit {
  private readonly api = inject(CrmApiService);

  page = 1;
  limit = 25;
  total = 0;

  readonly items = signal<ApprovalRequest[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

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
    this.success.set(null);
    try {
      const res = await firstValueFrom(this.api.listApprovals(this.page, this.limit));
      this.items.set(res.items);
      this.total = res.total;
      this.page = res.page;
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar aprobaciones');
    } finally {
      this.loading.set(false);
    }
  }

  async review(id: number, action: 'approve' | 'reject'): Promise<void> {
    const note = prompt(`Nota de ${action === 'approve' ? 'aprobación' : 'rechazo'} (opcional):`) ?? '';
    this.saving.set(true);
    this.error.set(null);
    try {
      if (action === 'approve') {
        await firstValueFrom(this.api.approveRequest(id, note || undefined));
        this.success.set(`Solicitud #${id} aprobada.`);
      } else {
        await firstValueFrom(this.api.rejectRequest(id, note || undefined));
        this.success.set(`Solicitud #${id} rechazada.`);
      }
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : `Error al ${action === 'approve' ? 'aprobar' : 'rechazar'}`);
    } finally {
      this.saving.set(false);
    }
  }
}
