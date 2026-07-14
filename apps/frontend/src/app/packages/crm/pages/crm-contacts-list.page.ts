import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Contact } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-contacts-list-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-contacts-list-page">
      <app-enterprise-page-header
        [title]="'crm.contacts.title' | t:lang()"
        [subtitle]="'crm.contacts.subtitle' | t:lang()"
      >
        <a class="btn btn--ghost" routerLink="/crm/dashboard">← CRM</a>
      </app-enterprise-page-header>

      <p class="muted">{{ 'crm.contacts.permissionNote' | t:lang() }}</p>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      <app-enterprise-section-card [title]="'crm.contacts.create' | t:lang()">
        <form class="form-grid" (ngSubmit)="create()">
          <app-enterprise-form-field [label]="'crm.contacts.fullName' | t:lang()" [required]="true">
            <input class="input" [(ngModel)]="form.full_name" name="full_name" required />
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'common.email' | t:lang()">
            <input class="input" [(ngModel)]="form.email" name="email" type="email" />
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'crm.prospects.phone' | t:lang()">
            <input class="input" [(ngModel)]="form.phone" name="phone" />
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'crm.prospects.company' | t:lang()">
            <input class="input" [(ngModel)]="form.company_name" name="company_name" />
          </app-enterprise-form-field>
          <div class="form-grid__actions">
            <button type="submit" class="btn btn--primary" [disabled]="!form.full_name.trim() || saving()">
              {{ (saving() ? 'crm.contacts.creating' : 'crm.contacts.create') | t:lang() }}
            </button>
          </div>
        </form>
      </app-enterprise-section-card>

      <app-enterprise-section-card [title]="'crm.contacts.list' | t:lang()">
        @if (loading()) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (contacts().length === 0) {
          <app-enterprise-empty-state
            [title]="'crm.contacts.empty' | t:lang()"
            [description]="'crm.contacts.emptyHint' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'common.email' | t:lang() }}</th>
                  <th>{{ 'crm.prospects.phone' | t:lang() }}</th>
                  <th>{{ 'crm.prospects.company' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (c of contacts(); track c.id) {
                  <tr>
                    <td>{{ c.full_name }}</td>
                    <td>{{ c.email || ('common.notAvailable' | t:lang()) }}</td>
                    <td>{{ c.phone || ('common.notAvailable' | t:lang()) }}</td>
                    <td>{{ c.company_name || ('common.notAvailable' | t:lang()) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      </app-enterprise-section-card>
    </div>
  `,
})
export class CrmContactsListPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

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
      this.success.set(this.i18n.t('crm.contacts.createdMsg'));
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear contacto');
    } finally {
      this.saving.set(false);
    }
  }
}
