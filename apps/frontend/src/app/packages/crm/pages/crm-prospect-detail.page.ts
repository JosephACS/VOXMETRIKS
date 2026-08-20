import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Contact, Prospect } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

const PROSPECT_STATUSES = ['contacted', 'qualified', 'disqualified', 'lost'];

@Component({
  selector: 'app-crm-prospect-detail-page',
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
    <div class="vx-enterprise crm-page" data-testid="crm-prospect-detail-page">
      <app-enterprise-page-header
        [title]="prospect()?.display_name || ('crm.prospectDetail.fallback' | t:{ id: prospectId }:lang())"
      >
        <a class="btn btn--ghost" routerLink="/crm/prospects">
          ← {{ 'crm.prospectDetail.back' | t:lang() }}
        </a>
        @if (prospect()) {
          <app-enterprise-status-badge [status]="prospect()!.status" />
          @if (prospect()!.status === 'qualified') {
            <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="createOpportunity()">
              {{ 'crm.prospectDetail.createOpportunity' | t:lang() }}
            </button>
          }
        }
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (prospect()) {
        <app-enterprise-section-card [title]="'crm.prospectDetail.title' | t:lang()">
          <form class="form-grid" (ngSubmit)="save()">
            <app-enterprise-form-field [label]="'common.name' | t:lang()" [required]="true">
              <input class="input" [(ngModel)]="editForm.display_name" name="display_name" required />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.prospects.company' | t:lang()">
              <input class="input" [(ngModel)]="editForm.company_name" name="company_name" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.email' | t:lang()">
              <input class="input" [(ngModel)]="editForm.email" name="email" type="email" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.prospects.phone' | t:lang()">
              <input class="input" [(ngModel)]="editForm.phone" name="phone" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.prospects.source' | t:lang()">
              <input class="input" [(ngModel)]="editForm.source" name="source" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.notes' | t:lang()">
              <textarea class="input" [(ngModel)]="editForm.notes" name="notes" rows="3"></textarea>
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="saving()">
                {{ (saving() ? 'common.saving' : 'crm.prospectDetail.save') | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'crm.prospectDetail.changeStatus' | t:lang()">
          <form class="form-grid">
            <app-enterprise-form-field [label]="'crm.prospectDetail.newStatus' | t:lang()">
              <select class="select" [(ngModel)]="newStatus" name="newStatus">
                @for (s of statuses; track s) {
                  <option [value]="s" [disabled]="s === prospect()!.status">{{ s | statusLabel }}</option>
                }
              </select>
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button
                type="button"
                class="btn btn--secondary"
                [disabled]="!newStatus || newStatus === prospect()!.status || saving()"
                (click)="transitionStatus()"
              >
                {{ 'crm.prospectDetail.applyStatus' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'crm.prospectDetail.linkContact' | t:lang()">
          @if (contacts().length) {
            <form class="form-grid">
              <app-enterprise-form-field [label]="'common.contact' | t:lang()">
                <select class="select" [(ngModel)]="selectedContactId" name="contactId">
                  <option [ngValue]="null">— {{ 'crm.prospectDetail.selectContact' | t:lang() }} —</option>
                  @for (c of contacts(); track c.id) {
                    <option [ngValue]="c.id">
                      {{ c.full_name }} ({{ c.email || c.phone || '#' + c.id }})
                    </option>
                  }
                </select>
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button
                  type="button"
                  class="btn btn--secondary"
                  [disabled]="selectedContactId == null || saving()"
                  (click)="linkContact()"
                >
                  {{ 'crm.prospectDetail.link' | t:lang() }}
                </button>
              </div>
            </form>
          } @else {
            <app-enterprise-empty-state
              [title]="'crm.prospectDetail.noContacts' | t:lang()"
              [ctaLabel]="'crm.prospectDetail.createContact' | t:lang()"
              [ctaLink]="'/crm/contacts'"
            />
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card>
          <div class="form-grid muted" style="font-size: 0.875rem">
            <div>
              <dt>{{ 'common.created' | t:lang() }}</dt>
              <dd>{{ prospect()!.created_at | localeDate:true }}</dd>
            </div>
            <div>
              <dt>{{ 'common.updated' | t:lang() }}</dt>
              <dd>{{ prospect()!.updated_at | localeDate:true }}</dd>
            </div>
            @if (prospect()!.owner_user_id) {
              <div>
                <dt>{{ 'common.owner' | t:lang() }}</dt>
                <dd>#{{ prospect()!.owner_user_id }}</dd>
              </div>
            }
          </div>
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class CrmProspectDetailPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

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
      this.success.set(this.i18n.t('crm.prospectDetail.updatedMsg'));
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
      this.success.set(this.i18n.t('crm.prospectDetail.statusChanged', { status: this.newStatus }));
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
      this.success.set(this.i18n.t('crm.prospectDetail.linkedMsg'));
      this.selectedContactId = null;
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al vincular contacto');
    } finally {
      this.saving.set(false);
    }
  }

  async createOpportunity(): Promise<void> {
    const p = this.prospect();
    if (!p || p.status !== 'qualified') return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const opp = await firstValueFrom(
        this.api.createOpportunity({
          prospect_id: this.prospectId,
          name: p.company_name?.trim() || p.display_name,
        }),
      );
      this.success.set(this.i18n.t('crm.prospectDetail.opportunityCreated'));
      await this.router.navigate(['/crm/opportunities', opp.id]);
    } catch (e) {
      this.error.set(
        e instanceof CrmApiError ? e.message : this.i18n.t('crm.prospectDetail.opportunityCreateError'),
      );
      this.saving.set(false);
    }
  }
}
