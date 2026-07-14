import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-cs-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  template: `
    <div class="vx-enterprise page">
      <h1>{{ 'customerSuccess.dashboard.title' | t:lang() }}</h1>
      <p class="subtitle">
        Rule-based health score (not AI). Academic SLA configs are not contractual.
      </p>
      <nav class="subnav">
        <a routerLink="/customer-success">Dashboard</a> |
        <a routerLink="/support">{{ 'support.list.title' | t:lang() }}</a>
      </nav>

      @if (!orgId) {
        <p class="error">Select an organization context.</p>
      } @else {
        <div class="actions">
          <button type="button" (click)="refresh()" [disabled]="busy">Refresh / calculate health</button>
          <button type="button" (click)="startOnboarding()" [disabled]="busy">Start onboarding</button>
          <button type="button" (click)="renewal()" [disabled]="busy">Evaluate renewal</button>
        </div>

        @if (loading) {
          <p>{{ 'common.loading' | t:lang() }}</p>
        } @else if (error) {
          <p class="error">{{ error }}</p>
        } @else if (success) {
          <p class="success">{{ success }}</p>
        }

        @if (health) {
          <section class="cs-card">
            <h2>Health</h2>
            <p>
              State:
              <span class="badge">{{ health.score_state || ('common.notAvailable' | t:lang()) }}</span>
            </p>
            <p>
              Score:
              @if (health.score == null) {
                <em>{{ 'common.notAvailable' | t:lang() }}</em>
              } @else {
                {{ health.score | number: '1.2-4' }}
              }
            </p>
            <p class="muted">{{ health.limitations || 'No limitations listed.' }}</p>
          </section>
        } @else if (!loading && !error) {
          <p class="empty-state">No health snapshot yet. Click calculate health.</p>
        }

        @if (dashboard) {
          <section class="cs-card">
            <h2>Overview</h2>
            <p>Open risks: {{ dashboard.open_risks ?? ('common.notAvailable' | t:lang()) }}</p>
            <p>Expansion opportunities: {{ dashboard.expansions ?? ('common.notAvailable' | t:lang()) }}</p>
            <p class="muted">{{ dashboard.label || ('customerSuccess.dashboard.title' | t:lang()) }}</p>
          </section>
        }

        <section class="cs-card">
          <h2>Risks</h2>
          <form class="inline-form" (ngSubmit)="createRisk()">
            <input [(ngModel)]="riskTitle" name="riskTitle" placeholder="Risk title" required />
            <select [(ngModel)]="riskSeverity" name="riskSeverity">
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
            <button type="submit" [disabled]="busy || !riskTitle.trim()">Create risk</button>
          </form>
          @if (risks.length === 0) {
            <p class="empty-state">{{ 'customerSuccess.dashboard.noRisks' | t:lang() }}</p>
          } @else {
            <ul>
              @for (r of risks; track $any(r).id) {
                <li>
                  <span class="badge">{{ $any(r).severity }}</span>
                  {{ $any(r).title }} — {{ $any(r).status }}
                  <button type="button" (click)="assignIntervention($any(r).id)" [disabled]="busy">
                    Assign intervention
                  </button>
                </li>
              }
            </ul>
          }
        </section>

        <section class="cs-card">
          <h2>Interventions</h2>
          @if (interventions.length === 0) {
            <p class="empty-state">No interventions.</p>
          } @else {
            <ul>
              @for (i of interventions; track $any(i).id) {
                <li>
                  {{ $any(i).title }} — <span class="badge">{{ $any(i).status }}</span>
                  @if ($any(i).status !== 'completed') {
                    <button type="button" (click)="completeIntervention($any(i).id)" [disabled]="busy">
                      Complete
                    </button>
                  }
                </li>
              }
            </ul>
          }
        </section>

        <section class="cs-card">
          <h2>Expansion</h2>
          <form class="inline-form" (ngSubmit)="createExpansion()">
            <input [(ngModel)]="expansionTitle" name="expansionTitle" placeholder="Expansion title" required />
            <button type="submit" [disabled]="busy || !expansionTitle.trim()">Create expansion</button>
          </form>
          @if (expansions.length === 0) {
            <p class="empty-state">No expansion opportunities.</p>
          } @else {
            <ul>
              @for (e of expansions; track $any(e).id) {
                <li>
                  {{ $any(e).title }} — {{ $any(e).status }}
                  @if ($any(e).estimated_value == null) {
                    <em>{{ 'common.notAvailable' | t:lang() }}</em>
                  } @else {
                    ({{ $any(e).estimated_value }})
                  }
                </li>
              }
            </ul>
          }
        </section>
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
  dashboard: { open_risks?: number; expansions?: number; label?: string; health?: unknown } | null = null;
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
            this.success = 'Health refreshed.';
          },
          error: (e) => {
            this.error = e?.error?.detail?.message || 'Dashboard denied or failed';
            this.loading = false;
            this.busy = false;
          },
        });
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Health calculation failed';
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
