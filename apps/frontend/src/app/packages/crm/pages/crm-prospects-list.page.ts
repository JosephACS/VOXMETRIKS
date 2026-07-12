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
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

const PROSPECT_STATUSES = ['new', 'contacted', 'qualified', 'disqualified', 'converted'];

@Component({
  selector: 'app-crm-prospects-list-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-prospects-list-page">
      <h1>{{ 'crm.prospects.title' | t:lang() }}</h1>
      <p class="lede">Lista de prospectos comerciales.</p>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      <!-- Filter & Create -->
      <div class="crm-card">
        <div style="display:flex;flex-wrap:wrap;gap:0.6rem;align-items:flex-end">
          <label style="flex:1;min-width:140px">
            <span>Filtrar por estado</span>
            <select [(ngModel)]="statusFilter" (ngModelChange)="applyFilter()">
              <option value="">Todos</option>
              @for (s of statuses; track s) {
                <option [value]="s">{{ s }}</option>
              }
            </select>
          </label>
          <button type="button" class="crm-btn" (click)="showCreate = !showCreate">
            {{ showCreate ? 'Cancelar' : '+ Nuevo prospecto' }}
          </button>
        </div>

        @if (showCreate) {
          <form class="crm-form" style="margin-top:1rem" (ngSubmit)="create()" #f="ngForm">
            <label>
              Nombre *
              <input [(ngModel)]="form.display_name" name="display_name" required
                placeholder="Nombre del prospecto" />
            </label>
            <label>
              Empresa
              <input [(ngModel)]="form.company_name" name="company_name" placeholder="Empresa" />
            </label>
            <label>
              Correo
              <input [(ngModel)]="form.email" name="email" type="email" placeholder="correo@ejemplo.com" />
            </label>
            <label>
              Teléfono
              <input [(ngModel)]="form.phone" name="phone" placeholder="+1 555 000 0000" />
            </label>
            <label>
              Fuente
              <input [(ngModel)]="form.source" name="source" placeholder="web, referido, etc." />
            </label>
            <label>
              Notas
              <textarea [(ngModel)]="form.notes" name="notes" rows="2"></textarea>
            </label>
            <div class="crm-actions">
              <button type="submit" class="crm-btn" [disabled]="!form.display_name || saving()">
                {{ saving() ? 'Guardando…' : 'Crear' }}
              </button>
            </div>
          </form>
        }
      </div>

      <!-- Table -->
      @if (loading()) {
        <p class="crm-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else if (!items().length) {
        <div class="crm-card"><p class="crm-muted">{{ 'crm.prospects.empty' | t:lang() }}.</p></div>
      } @else {
        <div class="crm-card" style="overflow-x:auto">
          <table class="crm-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Nombre</th>
                <th>Empresa</th>
                <th>Correo</th>
                <th>Estado</th>
                <th>Creado</th>
              </tr>
            </thead>
            <tbody>
              @for (p of items(); track p.id) {
                <tr>
                  <td>
                    <a class="crm-btn crm-btn--ghost"
                      style="padding:0.2rem 0.5rem;font-size:0.8rem"
                      [routerLink]="['/crm/prospects', p.id]">{{ p.id }}</a>
                  </td>
                  <td>
                    <a [routerLink]="['/crm/prospects', p.id]">{{ p.display_name }}</a>
                  </td>
                  <td>{{ p.company_name || '—' }}</td>
                  <td>{{ p.email || '—' }}</td>
                  <td>
                    <span class="crm-badge crm-badge--{{ p.status }}">{{ p.status }}</span>
                  </td>
                  <td class="crm-muted">{{ p.created_at | date: 'shortDate' }}</td>
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
export class CrmProspectsListPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);

  readonly statuses = PROSPECT_STATUSES;

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
    if (!this.form.display_name) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.createProspect(this.form));
      this.form = { display_name: '' };
      this.showCreate = false;
      this.success.set('Prospecto creado.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear prospecto');
    } finally {
      this.saving.set(false);
    }
  }
}
