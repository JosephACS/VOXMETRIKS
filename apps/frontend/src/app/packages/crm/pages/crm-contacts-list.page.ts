import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Contact } from '../models/crm.models';

@Component({
  selector: 'app-crm-contacts-list-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-contacts-list-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/dashboard">← CRM</a>
        <h1 style="margin:0">Contactos</h1>
      </div>
      <p class="crm-muted">Contactos comerciales vinculados a prospectos. Requiere permiso CRM.</p>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      <div class="crm-card">
        <h2>Nuevo contacto</h2>
        <form class="crm-form" (ngSubmit)="create()">
          <label>Nombre completo *
            <input [(ngModel)]="form.full_name" name="full_name" required />
          </label>
          <label>Email
            <input [(ngModel)]="form.email" name="email" type="email" />
          </label>
          <label>Teléfono
            <input [(ngModel)]="form.phone" name="phone" />
          </label>
          <label>Empresa
            <input [(ngModel)]="form.company_name" name="company_name" />
          </label>
          <div class="crm-actions">
            <button type="submit" class="crm-btn" [disabled]="!form.full_name.trim() || saving()">
              {{ saving() ? 'Creando…' : 'Crear contacto' }}
            </button>
          </div>
        </form>
      </div>

      <div class="crm-card">
        <h2>Listado</h2>
        @if (loading()) {
          <p class="crm-muted">Cargando…</p>
        } @else if (contacts().length === 0) {
          <p class="crm-muted">Sin contactos. Crea el primero arriba.</p>
        } @else {
          <table class="crm-table">
            <thead>
              <tr><th>Nombre</th><th>Email</th><th>Teléfono</th><th>Empresa</th></tr>
            </thead>
            <tbody>
              @for (c of contacts(); track c.id) {
                <tr>
                  <td>{{ c.full_name }}</td>
                  <td>{{ c.email || 'No disponible' }}</td>
                  <td>{{ c.phone || 'No disponible' }}</td>
                  <td>{{ c.company_name || 'No disponible' }}</td>
                </tr>
              }
            </tbody>
          </table>
        }
      </div>
    </section>
  `,
})
export class CrmContactsListPageComponent implements OnInit {
  private readonly api = inject(CrmApiService);

  form = { full_name: '', email: '', phone: '', company_name: '' };
  readonly contacts = signal<Contact[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const res = await firstValueFrom(this.api.listContacts(1, 100));
      this.contacts.set(res.items ?? []);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar contactos');
    } finally {
      this.loading.set(false);
    }
  }

  async create(): Promise<void> {
    if (!this.form.full_name.trim()) return;
    this.saving.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      await firstValueFrom(
        this.api.createContact({
          full_name: this.form.full_name.trim(),
          email: this.form.email || undefined,
          phone: this.form.phone || undefined,
          company_name: this.form.company_name || undefined,
        }),
      );
      this.form = { full_name: '', email: '', phone: '', company_name: '' };
      this.success.set('Contacto creado.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear contacto');
    } finally {
      this.saving.set(false);
    }
  }
}
