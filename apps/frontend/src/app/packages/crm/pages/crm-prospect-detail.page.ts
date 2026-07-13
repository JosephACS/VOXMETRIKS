import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Contact, Prospect } from '../models/crm.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
const PROSPECT_STATUSES = ['new', 'contacted', 'qualified', 'disqualified', 'converted'];

@Component({
  selector: 'app-crm-prospect-detail-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-prospect-detail-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/prospects">← {{ 'crm.prospects.title' | t:lang() }}</a>
        <h1 style="margin:0">
          {{ prospect()?.display_name || 'Prospecto #' + prospectId }}
        </h1>
        @if (prospect()) {
          <span class="crm-badge crm-badge--{{ prospect()!.status }}">{{ prospect()!.status }}</span>
        }
      </div>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else if (prospect()) {
        <!-- Edit form -->
        <div class="crm-card">
          <h2>Datos del prospecto</h2>
          <form class="crm-form" (ngSubmit)="save()">
            <label>Nombre *
              <input [(ngModel)]="editForm.display_name" name="display_name" required />
            </label>
            <label>Empresa
              <input [(ngModel)]="editForm.company_name" name="company_name" />
            </label>
            <label>Correo
              <input [(ngModel)]="editForm.email" name="email" type="email" />
            </label>
            <label>Teléfono
              <input [(ngModel)]="editForm.phone" name="phone" />
            </label>
            <label>Fuente
              <input [(ngModel)]="editForm.source" name="source" />
            </label>
            <label>Notas
              <textarea [(ngModel)]="editForm.notes" name="notes" rows="3"></textarea>
            </label>
            <div class="crm-actions">
              <button type="submit" class="crm-btn" [disabled]="saving()">
                {{ saving() ? 'Guardando…' : 'Guardar cambios' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Status transition -->
        <div class="crm-card">
          <h2>Cambiar estado</h2>
          <div class="crm-form">
            <label>Nuevo estado
              <select [(ngModel)]="newStatus" name="newStatus">
                @for (s of statuses; track s) {
                  <option [value]="s" [disabled]="s === prospect()!.status">{{ s }}</option>
                }
              </select>
            </label>
            <div class="crm-actions">
              <button type="button" class="crm-btn crm-btn--ghost"
                [disabled]="!newStatus || newStatus === prospect()!.status || saving()"
                (click)="transitionStatus()">
                Aplicar estado
              </button>
            </div>
          </div>
        </div>

        <!-- Link contact -->
        <div class="crm-card">
          <h2>Vincular contacto</h2>
          @if (contacts().length) {
            <div class="crm-form">
              <label>Contacto
                <select [(ngModel)]="selectedContactId" name="contactId">
                  <option [ngValue]="null">— Selecciona —</option>
                  @for (c of contacts(); track c.id) {
                    <option [ngValue]="c.id">{{ c.full_name }} ({{ c.email || c.phone || '#' + c.id }})</option>
                  }
                </select>
              </label>
              <div class="crm-actions">
                <button type="button" class="crm-btn crm-btn--ghost"
                  [disabled]="selectedContactId == null || saving()"
                  (click)="linkContact()">
                  Vincular
                </button>
              </div>
            </div>
          } @else {
            <p class="crm-muted">No hay contactos disponibles.</p>
            <a class="crm-btn crm-btn--ghost" routerLink="/crm/contacts">Crear contacto</a>
          }
        </div>

        <!-- Prospect metadata -->
        <div class="crm-card crm-muted" style="font-size:0.8rem">
          <p>Creado: {{ prospect()!.created_at | date:'medium' }}</p>
          <p>Actualizado: {{ prospect()!.updated_at | date:'medium' }}</p>
          @if (prospect()!.owner_user_id) {
            <p>Propietario: #{{ prospect()!.owner_user_id }}</p>
          }
        </div>
      }
    </section>
  `,
})
export class CrmProspectDetailPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);

  readonly statuses = PROSPECT_STATUSES;

  prospectId = 0;
  newStatus = '';
  selectedContactId: number | null = null;

  editForm = { display_name: '', company_name: '', email: '', phone: '', source: '', notes: '' };

  readonly prospect = signal<Prospect | null>(null);
  readonly contacts = signal<Contact[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.prospectId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const [p, contactsRes] = await Promise.all([
        firstValueFrom(this.api.getProspect(this.prospectId)),
        firstValueFrom(this.api.listContacts(1, 100)),
      ]);
      this.prospect.set(p);
      this.newStatus = p.status;
      this.editForm = {
        display_name: p.display_name,
        company_name: p.company_name ?? '',
        email: p.email ?? '',
        phone: p.phone ?? '',
        source: p.source ?? '',
        notes: p.notes ?? '',
      };
      this.contacts.set(contactsRes.items);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar prospecto');
    } finally {
      this.loading.set(false);
    }
  }

  async save(): Promise<void> {
    if (!this.editForm.display_name) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const updated = await firstValueFrom(
        this.api.updateProspect(this.prospectId, {
          display_name: this.editForm.display_name,
          company_name: this.editForm.company_name || undefined,
          email: this.editForm.email || undefined,
          phone: this.editForm.phone || undefined,
          source: this.editForm.source || undefined,
          notes: this.editForm.notes || undefined,
        }),
      );
      this.prospect.set(updated);
      this.success.set('Prospecto actualizado.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al guardar');
    } finally {
      this.saving.set(false);
    }
  }

  async transitionStatus(): Promise<void> {
    if (!this.newStatus) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const updated = await firstValueFrom(
        this.api.transitionProspectStatus(this.prospectId, this.newStatus),
      );
      this.prospect.set(updated);
      this.success.set(`Estado cambiado a "${this.newStatus}".`);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cambiar estado');
    } finally {
      this.saving.set(false);
    }
  }

  async linkContact(): Promise<void> {
    if (this.selectedContactId == null) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.linkContactToProspect(this.prospectId, this.selectedContactId));
      this.success.set('Contacto vinculado.');
      this.selectedContactId = null;
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al vincular contacto');
    } finally {
      this.saving.set(false);
    }
  }
}
