import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Quotation, QuotationVersion, QuotationItem, QuotationItemCreateRequest } from '../models/crm.models';

@Component({
  selector: 'app-crm-quotation-editor-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-quotation-editor-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/opportunities">← Oportunidades</a>
        <h1 style="margin:0">Cotización #{{ quotationId }}</h1>
        @if (quotation()) {
          <span class="crm-badge crm-badge--{{ quotation()!.status }}">{{ quotation()!.status }}</span>
        }
      </div>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">Cargando…</p>
      } @else if (quotation()) {
        <!-- Quotation summary -->
        <div class="crm-card">
          <h2>Resumen</h2>
          <p class="crm-muted">
            Oportunidad: #{{ quotation()!.opportunity_id }} · Moneda: {{ quotation()!.currency || '—' }} ·
            Versión actual: v{{ quotation()!.current_version_no ?? '—' }}
          </p>
          @if (quotation()!.notes) {
            <p>{{ quotation()!.notes }}</p>
          }
          <!-- Create new version -->
          <div class="crm-actions" style="margin-top:0.6rem">
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="saving()"
              (click)="createVersion()">
              + Nueva versión
            </button>
          </div>
        </div>

        <!-- Versions -->
        @if (versions().length) {
          @for (v of versions(); track v.id) {
            <div class="crm-card">
              <div style="display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.5rem">
                <h2 style="margin:0">Versión {{ v.version_no }}</h2>
                <span class="crm-badge crm-badge--{{ v.status }}">{{ v.status }}</span>
                @if (v.is_immutable) {
                  <span class="crm-readonly-note">(enviada — solo lectura)</span>
                }
              </div>

              <p class="crm-muted">
                Subtotal: {{ v.subtotal ?? 0 | number:'1.2-2' }} ·
                Descuento: {{ v.discount_pct ?? 0 }}% ·
                Total: {{ v.total ?? 0 | number:'1.2-2' }}
                @if (v.discount_requires_approval) {
                  <span class="crm-badge crm-badge--pending" style="margin-left:0.5rem">Requiere aprobación</span>
                }
              </p>

              @if (v.sent_at) {
                <p class="crm-muted">Enviada: {{ v.sent_at | date:'medium' }}</p>
              }
              @if (v.accepted_at) {
                <p class="crm-muted">Aceptada: {{ v.accepted_at | date:'medium' }}</p>
              }
              @if (v.rejected_at) {
                <p class="crm-muted">Rechazada: {{ v.rejected_at | date:'medium' }}</p>
              }

              <!-- Items table -->
              @if (itemsMap()[v.id]?.length) {
                <table class="crm-table" style="margin-bottom:0.6rem">
                  <thead>
                    <tr><th>Descripción</th><th>Cant.</th><th>Precio</th><th>Desc %</th><th>Total línea</th></tr>
                  </thead>
                  <tbody>
                    @for (item of itemsMap()[v.id]; track item.id) {
                      <tr>
                        <td>{{ item.description }}</td>
                        <td>{{ item.quantity }}</td>
                        <td>{{ item.unit_price | number:'1.2-2' }}</td>
                        <td>{{ item.discount_pct ?? 0 }}%</td>
                        <td>{{ item.line_total ?? 0 | number:'1.2-2' }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              } @else {
                <p class="crm-muted">Sin ítems.</p>
              }

              <!-- Add item (only if not immutable) -->
              @if (!v.is_immutable) {
                <button type="button" class="crm-btn crm-btn--ghost"
                  (click)="toggleItemForm(v.id)">
                  {{ activeItemForm === v.id ? 'Cancelar' : '+ Añadir ítem' }}
                </button>
                @if (activeItemForm === v.id) {
                  <form class="crm-form" style="margin-top:0.75rem" (ngSubmit)="addItem(v.id)">
                    <label>Descripción *
                      <input [(ngModel)]="itemForm.description" name="description" required />
                    </label>
                    <label>Cantidad *
                      <input [(ngModel)]="itemForm.quantity" name="quantity" type="number" min="1" required />
                    </label>
                    <label>Precio unitario *
                      <input [(ngModel)]="itemForm.unit_price" name="unit_price" type="number" min="0" step="0.01" required />
                    </label>
                    <label>Descuento %
                      <input [(ngModel)]="itemForm.discount_pct" name="discount_pct" type="number" min="0" max="100" step="0.01" />
                    </label>
                    <div class="crm-actions">
                      <button type="submit" class="crm-btn"
                        [disabled]="!itemForm.description || !itemForm.quantity || saving()">
                        Añadir
                      </button>
                    </div>
                  </form>
                }

                <div class="crm-actions" style="margin-top:0.6rem">
                  <button type="button" class="crm-btn" [disabled]="saving()"
                    (click)="send(v.id)">
                    Enviar versión
                  </button>
                  <button type="button" class="crm-btn crm-btn--warn" [disabled]="saving()"
                    (click)="requestApproval(v.id)">
                    Solicitar aprobación descuento
                  </button>
                </div>
              }
            </div>
          }
        } @else {
          <div class="crm-card"><p class="crm-muted">Sin versiones. Crea la primera.</p></div>
        }
      }
    </section>
  `,
})
export class CrmQuotationEditorPageComponent implements OnInit {
  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);

  quotationId = 0;
  activeItemForm: number | null = null;
  approvalReason = '';

  itemForm: QuotationItemCreateRequest = { description: '', quantity: 1, unit_price: 0 };

  readonly quotation = signal<Quotation | null>(null);
  readonly versions = signal<QuotationVersion[]>([]);
  readonly itemsMap = signal<Record<number, QuotationItem[]>>({});
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.quotationId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const [q, vers] = await Promise.all([
        firstValueFrom(this.api.getQuotation(this.quotationId)),
        firstValueFrom(this.api.listQuotationVersions(this.quotationId)),
      ]);
      this.quotation.set(q);
      this.versions.set(vers);
      // Load items for each version
      const map: Record<number, QuotationItem[]> = {};
      await Promise.all(
        vers.map(async (v) => {
          try {
            map[v.id] = await firstValueFrom(this.api.listQuotationItems(v.id));
          } catch {
            map[v.id] = [];
          }
        }),
      );
      this.itemsMap.set(map);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar cotización');
    } finally {
      this.loading.set(false);
    }
  }

  async createVersion(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.createQuotationVersion(this.quotationId));
      this.success.set('Nueva versión creada.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear versión');
    } finally {
      this.saving.set(false);
    }
  }

  toggleItemForm(versionId: number): void {
    this.activeItemForm = this.activeItemForm === versionId ? null : versionId;
    this.itemForm = { description: '', quantity: 1, unit_price: 0 };
  }

  async addItem(versionId: number): Promise<void> {
    if (!this.itemForm.description || !this.itemForm.quantity) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const item = await firstValueFrom(this.api.addQuotationItem(versionId, this.itemForm));
      const map = { ...this.itemsMap() };
      map[versionId] = [...(map[versionId] ?? []), item];
      this.itemsMap.set(map);
      this.activeItemForm = null;
      this.success.set('Ítem añadido.');
      // Reload to get updated totals
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al añadir ítem');
    } finally {
      this.saving.set(false);
    }
  }

  async send(versionId: number): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.sendQuotationVersion(versionId));
      this.success.set('Versión enviada. Ya no es editable.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al enviar versión');
    } finally {
      this.saving.set(false);
    }
  }

  async requestApproval(versionId: number): Promise<void> {
    const reason = prompt('Motivo de la solicitud de aprobación de descuento:') ?? '';
    if (!reason) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.requestDiscountApproval(versionId, reason));
      this.success.set('Solicitud de aprobación enviada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al solicitar aprobación');
    } finally {
      this.saving.set(false);
    }
  }
}
