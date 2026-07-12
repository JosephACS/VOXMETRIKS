import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-cs-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page">
      <h1>Customer Success</h1>
      <p class="subtitle">
        Rule-based health score (not AI). Academic SLA configs are not contractual.
      </p>
      <nav class="subnav">
        <a routerLink="/customer-success">Dashboard</a> |
        <a routerLink="/support">Support</a>
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
          <p>Loading…</p>
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
              <span class="badge">{{ health.score_state || 'No disponible' }}</span>
            </p>
            <p>
              Score:
              @if (health.score == null) {
                <em>No disponible</em>
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
            <p>Open risks: {{ dashboard.open_risks ?? 'No disponible' }}</p>
            <p>Expansion opportunities: {{ dashboard.expansions ?? 'No disponible' }}</p>
            <p class="muted">{{ dashboard.label || 'Customer Success academic dashboard' }}</p>
          </section>
        }
      }
    </div>
  `,
})
export class CsDashboardPage implements OnInit {
  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  dashboard: { open_risks?: number; expansions?: number; label?: string; health?: unknown } | null = null;
  health: {
    score?: number | null;
    score_state?: string;
    limitations?: string;
  } | null = null;
  loading = false;
  busy = false;
  error = '';
  success = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (this.orgId) this.refresh();
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
}
