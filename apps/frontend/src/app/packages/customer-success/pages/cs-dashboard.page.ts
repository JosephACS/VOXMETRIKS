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
      <p class="subtitle">Rule-based health (not AI). Academic SLA configs are not contractual.</p>
      <nav class="subnav"><a routerLink="/customer-success">Dashboard</a> | <a routerLink="/support">Support</a></nav>
      @if (!orgId) { <p class="error">Select an organization.</p> }
      @else {
        <button type="button" (click)="refresh()">Refresh / calculate health</button>
        <button type="button" (click)="startOnboarding()">Start onboarding</button>
        <button type="button" (click)="renewal()">Evaluate renewal</button>
        @if (loading) { <p>Loading…</p> }
        @else if (error) { <p class="error">{{ error }}</p> }
        @else if (data) {
          <pre>{{ data | json }}</pre>
        }
      }
    </div>
  `,
})
export class CsDashboardPage implements OnInit {
  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);
  orgId: number | null = null;
  data: unknown = null;
  loading = false;
  error = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (this.orgId) this.refresh();
  }

  refresh(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.api.calculateHealth(this.orgId).subscribe({
      next: () => {
        this.api.dashboard(this.orgId!).subscribe({
          next: (d) => {
            this.data = d;
            this.loading = false;
          },
          error: (e) => {
            this.error = e?.error?.detail?.message || 'Denied';
            this.loading = false;
          },
        });
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Health failed';
        this.loading = false;
      },
    });
  }

  startOnboarding(): void {
    if (!this.orgId) return;
    this.api.createOnboarding(this.orgId).subscribe({
      next: () => this.refresh(),
      error: (e) => (this.error = e?.error?.detail?.message || 'Onboarding failed'),
    });
  }

  renewal(): void {
    if (!this.orgId) return;
    this.api.evaluateRenewal(this.orgId).subscribe({
      next: () => this.refresh(),
      error: (e) => (this.error = e?.error?.detail?.message || 'Renewal failed'),
    });
  }
}
