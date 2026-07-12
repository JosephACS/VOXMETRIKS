import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CampaignsApiService } from '../services/campaigns-api.service';
import { Campaign } from '../models/campaigns.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-campaigns-list',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <div class="campaigns-list-page">
      <h1>Campaigns</h1>
      <p class="subtitle">Marketing campaigns with budgets, expenses, and ROI tracking.</p>

      <form [formGroup]="createForm" (ngSubmit)="createCampaign()" class="create-form">
        <input formControlName="name" placeholder="Campaign name" class="input" />
        <input formControlName="market" placeholder="Market (optional)" class="input" />
        <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">Create Campaign</button>
      </form>

      @if (error) { <p class="error">{{ error }}</p> }
      @if (loading) { <p>Loading…</p> }
      @else if (campaigns.length === 0) { <p>No campaigns yet.</p> }
      @else {
        <table class="campaigns-table">
          <thead>
            <tr><th>Name</th><th>Status</th><th>Market</th><th></th></tr>
          </thead>
          <tbody>
            @for (c of campaigns; track c.id) {
              <tr>
                <td>{{ c.name }}</td>
                <td><span class="badge">{{ c.status }}</span></td>
                <td>{{ c.market || '—' }}</td>
                <td><a [routerLink]="['/campaigns', c.id]">View</a></td>
              </tr>
            }
          </tbody>
        </table>
        <p class="total">Total: {{ total }}</p>
      }
    </div>
  `,
})
export class CampaignsListPage implements OnInit {
  private api = inject(CampaignsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  campaigns: Campaign[] = [];
  total = 0;
  loading = false;
  error: string | null = null;

  createForm = this.fb.group({ name: ['', Validators.required], market: [''] });

  ngOnInit(): void { this.load(); }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) { this.error = 'Select an organization'; return; }
    this.loading = true;
    this.api.list(orgId).subscribe({
      next: (r) => { this.campaigns = r.items; this.total = r.total; this.loading = false; },
      error: (e) => { this.error = e?.error?.message || 'Failed to load'; this.loading = false; },
    });
  }

  createCampaign(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId || this.createForm.invalid) return;
    const v = this.createForm.value;
    this.api.create(orgId, { name: v.name!, market: v.market || undefined }).subscribe({
      next: () => { this.createForm.reset(); this.load(); },
      error: (e) => { this.error = e?.error?.message || 'Create failed'; },
    });
  }
}
