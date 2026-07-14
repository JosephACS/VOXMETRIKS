import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CampaignsApiService } from '../services/campaigns-api.service';
import { Campaign } from '../models/campaigns.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-campaigns-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise campaigns-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'campaigns.list.title' | t:lang()"
          [subtitle]="'campaigns.list.subtitle' | t:lang()"
        />

        <app-enterprise-section-card [title]="'campaigns.list.create' | t:lang()">
          <form [formGroup]="createForm" (ngSubmit)="createCampaign()" class="form-grid">
            <app-enterprise-form-field [label]="'campaigns.list.name' | t:lang()" [required]="true">
              <input formControlName="name" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'campaigns.list.market' | t:lang()">
              <input formControlName="market" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
                {{ 'campaigns.list.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (campaigns.length === 0) {
          <app-enterprise-empty-state
            [title]="'campaigns.list.emptyTitle' | t:lang()"
            [description]="'campaigns.list.emptyBody' | t:lang()"
            [ctaLabel]="'campaigns.list.create' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'campaigns.list.market' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (c of campaigns; track c.id) {
                  <tr>
                    <td>{{ c.name }}</td>
                    <td><app-enterprise-status-badge [status]="c.status" /></td>
                    <td>{{ c.market || ('common.notAvailable' | t:lang()) }}</td>
                    <td>
                      <a [routerLink]="['/campaigns', c.id]" class="btn btn--ghost btn--sm">
                        {{ 'common.view' | t:lang() }}
                      </a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
          <p class="muted">{{ 'campaigns.list.total' | t:lang() }}: {{ total }}</p>
        }
      }
    </div>
  `,
})
export class CampaignsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CampaignsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  campaigns: Campaign[] = [];
  total = 0;
  loading = false;
  error: string | null = null;
  orgId: number | null = null;

  createForm = this.fb.group({ name: ['', Validators.required], market: [''] });

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) {
      this.orgId = null;
      return;
    }
    this.orgId = orgId;
    this.loading = true;
    this.api.list(orgId).subscribe({
      next: (r) => {
        this.campaigns = r.items;
        this.total = r.total;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.message || 'Failed to load';
        this.loading = false;
      },
    });
  }

  createCampaign(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId || this.createForm.invalid) return;
    const v = this.createForm.value;
    this.api.create(orgId, { name: v.name!, market: v.market || undefined }).subscribe({
      next: () => {
        this.createForm.reset();
        this.load();
      },
      error: (e) => {
        this.error = e?.error?.message || 'Create failed';
      },
    });
  }
}
