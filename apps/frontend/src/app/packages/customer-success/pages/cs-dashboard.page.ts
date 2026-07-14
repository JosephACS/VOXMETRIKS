import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-cs-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise cs-dashboard-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'customerSuccess.dashboard.title' | t:lang()"
          [subtitle]="'customerSuccess.dashboard.subtitle' | t:lang()"
        >
          <a routerLink="/support" class="btn btn--secondary">{{ 'support.list.title' | t:lang() }}</a>
        </app-enterprise-page-header>

        <app-enterprise-action-bar>
          <button type="button" class="btn btn--secondary" (click)="refresh()" [disabled]="busy">
            {{ 'customerSuccess.dashboard.refresh' | t:lang() }}
          </button>
          <button type="button" class="btn btn--secondary" (click)="startOnboarding()" [disabled]="busy">
            {{ 'customerSuccess.dashboard.startOnboarding' | t:lang() }}
          </button>
          <button type="button" class="btn btn--secondary" (click)="renewal()" [disabled]="busy">
            {{ 'customerSuccess.dashboard.evaluateRenewal' | t:lang() }}
          </button>
        </app-enterprise-action-bar>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="refresh()" />
        } @else if (success) {
          <div class="alert alert--success" role="status">{{ success }}</div>
        }

        @if (health) {
          <app-enterprise-section-card [title]="'customerSuccess.health' | t:lang()">
            <div class="form-grid">
              <div>
                <dt>{{ 'customerSuccess.dashboard.state' | t:lang() }}</dt>
                <dd>
                  <app-enterprise-status-badge
                    [status]="health.score_state || 'draft'"
                    [label]="health.score_state || ('common.notAvailable' | t:lang())"
                  />
                </dd>
              </div>
              <div>
                <dt>{{ 'customerSuccess.dashboard.score' | t:lang() }}</dt>
                <dd>
                  @if (health.score == null) {
                    {{ 'common.notAvailable' | t:lang() }}
                  } @else {
                    {{ health.score | number: '1.2-4' }}
                  }
                </dd>
              </div>
            </div>
            <p class="muted">
              {{ health.limitations || ('customerSuccess.dashboard.noLimitations' | t:lang()) }}
            </p>
          </app-enterprise-section-card>
        } @else if (!loading && !error) {
          <app-enterprise-empty-state
            [title]="'customerSuccess.dashboard.noHealth' | t:lang()"
            [ctaLabel]="'customerSuccess.dashboard.refresh' | t:lang()"
            (ctaClick)="refresh()"
          />
        }

        @if (dashboard) {
          <app-enterprise-section-card [title]="'customerSuccess.dashboard.overview' | t:lang()">
            <p>
              {{ 'customerSuccess.dashboard.openRisks' | t:lang() }}:
              {{ dashboard.open_risks ?? ('common.notAvailable' | t:lang()) }}
            </p>
            <p>
              {{ 'customerSuccess.dashboard.expansions' | t:lang() }}:
              {{ dashboard.expansions ?? ('common.notAvailable' | t:lang()) }}
            </p>
            <p class="muted">
              {{ dashboard.label || ('customerSuccess.dashboard.title' | t:lang()) }}
            </p>
          </app-enterprise-section-card>
        }

        <app-enterprise-section-card [title]="'customerSuccess.dashboard.risks' | t:lang()">
          <form class="form-grid" (ngSubmit)="createRisk()">
            <app-enterprise-form-field
              [label]="'customerSuccess.dashboard.riskTitle' | t:lang()"
              [required]="true"
            >
              <input [(ngModel)]="riskTitle" name="riskTitle" class="input" required />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'businessAnalytics.alerts.severity' | t:lang()">
              <select [(ngModel)]="riskSeverity" name="riskSeverity" class="select">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button
                type="submit"
                class="btn btn--primary"
                [disabled]="busy || !riskTitle.trim()"
              >
                {{ 'customerSuccess.dashboard.createRisk' | t:lang() }}
              </button>
            </div>
          </form>
          @if (risks.length === 0) {
            <app-enterprise-empty-state [title]="'customerSuccess.dashboard.noRisks' | t:lang()" />
          } @else {
            <ul class="ent-list">
              @for (r of risks; track $any(r).id) {
                <li>
                  <app-enterprise-status-badge [status]="$any(r).severity" />
                  {{ $any(r).title }} —
                  <app-enterprise-status-badge [status]="$any(r).status" />
                  <button
                    type="button"
                    class="btn btn--sm"
                    (click)="assignIntervention($any(r).id)"
                    [disabled]="busy"
                  >
                    {{ 'customerSuccess.dashboard.assignIntervention' | t:lang() }}
                  </button>
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'customerSuccess.dashboard.interventions' | t:lang()">
          @if (interventions.length === 0) {
            <app-enterprise-empty-state
              [title]="'customerSuccess.dashboard.noInterventions' | t:lang()"
            />
          } @else {
            <ul class="ent-list">
              @for (i of interventions; track $any(i).id) {
                <li>
                  {{ $any(i).title }} —
                  <app-enterprise-status-badge [status]="$any(i).status" />
                  @if ($any(i).status !== 'completed') {
                    <button
                      type="button"
                      class="btn btn--sm"
                      (click)="completeIntervention($any(i).id)"
                      [disabled]="busy"
                    >
                      {{ 'customerSuccess.dashboard.complete' | t:lang() }}
                    </button>
                  }
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'customerSuccess.expansion' | t:lang()">
          <form class="form-grid" (ngSubmit)="createExpansion()">
            <app-enterprise-form-field
              [label]="'customerSuccess.dashboard.expansionTitle' | t:lang()"
              [required]="true"
            >
              <input [(ngModel)]="expansionTitle" name="expansionTitle" class="input" required />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button
                type="submit"
                class="btn btn--primary"
                [disabled]="busy || !expansionTitle.trim()"
              >
                {{ 'customerSuccess.dashboard.createExpansion' | t:lang() }}
              </button>
            </div>
          </form>
          @if (expansions.length === 0) {
            <app-enterprise-empty-state
              [title]="'customerSuccess.dashboard.noExpansions' | t:lang()"
            />
          } @else {
            <ul class="ent-list">
              @for (e of expansions; track $any(e).id) {
                <li>
                  {{ $any(e).title }} —
                  <app-enterprise-status-badge [status]="$any(e).status" />
                  @if ($any(e).estimated_value == null) {
                    <em>{{ 'common.notAvailable' | t:lang() }}</em>
                  } @else {
                    ({{ $any(e).estimated_value }})
                  }
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class CsDashboardPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  dashboard: { open_risks?: number; expansions?: number; label?: string; health?: unknown } | null =
    null;
  health: {
    score?: number | null;
    score_state?: string;
    limitations?: string;
  } | null = null;
  risks: unknown[] = [];
  interventions: unknown[] = [];
  expansions: unknown[] = [];
  riskTitle = '';
  riskSeverity = 'medium';
  expansionTitle = '';
  loading = false;
  busy = false;
  error = '';
  success = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (this.orgId) this.refresh();
  }

  private loadLists(orgId: number): void {
    this.api.listRisks(orgId).subscribe({
      next: (r) => (this.risks = r || []),
      error: () => (this.risks = []),
    });
    this.api.listInterventions(orgId).subscribe({
      next: (i) => (this.interventions = i || []),
      error: () => (this.interventions = []),
    });
    this.api.listExpansions(orgId).subscribe({
      next: (e) => (this.expansions = e || []),
      error: () => (this.expansions = []),
    });
  }

  refresh(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.busy = true;
    this.error = '';
    this.success = '';
    this.api.calculateHealth(this.orgId).subscribe({
      next: (h) => {
        this.health = h as typeof this.health;
        this.api.dashboard(this.orgId!).subscribe({
          next: (d) => {
            this.dashboard = d as typeof this.dashboard;
            this.loadLists(this.orgId!);
            this.loading = false;
            this.busy = false;
            this.success = this.i18n.t('customerSuccess.dashboard.healthRefreshed');
          },
          error: (e) => {
            this.error = e?.error?.detail?.message || 'Dashboard denied or failed';
            this.loading = false;
            this.busy = false;
          },
        });
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('customerSuccess.dashboard.healthFailed');
        this.loading = false;
        this.busy = false;
      },
    });
  }

  startOnboarding(): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.createOnboarding(this.orgId).subscribe({
      next: () => {
        this.busy = false;
        this.success = 'Onboarding created.';
        this.refresh();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Onboarding failed';
        this.busy = false;
      },
    });
  }

  renewal(): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.evaluateRenewal(this.orgId).subscribe({
      next: () => {
        this.busy = false;
        this.success = 'Renewal evaluated.';
        this.refresh();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Renewal failed';
        this.busy = false;
      },
    });
  }

  createRisk(): void {
    if (!this.orgId || !this.riskTitle.trim()) return;
    this.busy = true;
    this.api.createRisk(this.orgId, this.riskTitle.trim(), this.riskSeverity).subscribe({
      next: () => {
        this.riskTitle = '';
        this.busy = false;
        this.success = 'Risk created.';
        this.loadLists(this.orgId!);
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Create risk failed';
        this.busy = false;
      },
    });
  }

  assignIntervention(riskId: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.createIntervention(this.orgId, `Intervention for risk #${riskId}`, riskId).subscribe({
      next: () => {
        this.busy = false;
        this.success = 'Intervention assigned.';
        this.loadLists(this.orgId!);
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Intervention failed';
        this.busy = false;
      },
    });
  }

  completeIntervention(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.completeIntervention(this.orgId, id).subscribe({
      next: () => {
        this.busy = false;
        this.success = 'Intervention completed.';
        this.loadLists(this.orgId!);
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Complete failed';
        this.busy = false;
      },
    });
  }

  createExpansion(): void {
    if (!this.orgId || !this.expansionTitle.trim()) return;
    this.busy = true;
    this.api.createExpansion(this.orgId, this.expansionTitle.trim()).subscribe({
      next: () => {
        this.expansionTitle = '';
        this.busy = false;
        this.success = 'Expansion created.';
        this.loadLists(this.orgId!);
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Expansion failed';
        this.busy = false;
      },
    });
  }
}
