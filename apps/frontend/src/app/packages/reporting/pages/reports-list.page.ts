import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { ExecutiveReport, ReportDefinition } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-reports-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page">
      <h1>Executive Reports</h1>
      <p class="subtitle">Generate immutable executive snapshots from versioned KPIs. Not a certified statement.</p>
      <nav class="subnav">
        <a routerLink="/reports">Reports</a> |
        <a routerLink="/business-decisions">Decisions</a>
      </nav>

      @if (!orgId) { <p class="error">Select an organization context.</p> }
      @else {
        <section>
          <h2>New definition</h2>
          <input [(ngModel)]="code" placeholder="code" />
          <input [(ngModel)]="title" placeholder="title" />
          <button type="button" (click)="createAndGenerate()" [disabled]="busy">Create &amp; generate</button>
        </section>

        @if (loading) { <p>Loading…</p> }
        @else if (error) { <p class="error">{{ error }}</p> }
        @else if (!reports.length) { <p>No executive reports yet.</p> }
        @else {
          <ul>
            @for (r of reports; track r.id) {
              <li>
                <a [routerLink]="['/reports', r.id]">{{ r.title }}</a>
                — {{ r.status }}
              </li>
            }
          </ul>
        }
      }
    </div>
  `,
})
export class ReportsListPage implements OnInit {
  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  reports: ExecutiveReport[] = [];
  definitions: ReportDefinition[] = [];
  code = 'monthly-exec';
  title = 'Monthly Executive';
  loading = false;
  busy = false;
  error = '';

  ngOnInit(): void {
    const org = this.orgCtx.activeOrganization();
    this.orgId = org?.id ?? null;
    if (this.orgId) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = '';
    this.api.listExecutive(this.orgId).subscribe({
      next: (p) => {
        this.reports = p.items || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || e?.message || 'Failed to load reports';
        this.loading = false;
      },
    });
  }

  createAndGenerate(): void {
    if (!this.orgId || !this.code || !this.title) return;
    this.busy = true;
    this.api.createDefinition(this.orgId, { code: this.code, title: this.title }).subscribe({
      next: (d) => {
        this.api.requestGeneration(this.orgId!, d.id).subscribe({
          next: (g) => {
            this.api.generate(this.orgId!, g.id).subscribe({
              next: () => {
                this.busy = false;
                this.reload();
              },
              error: (e) => {
                this.error = e?.error?.detail?.message || 'Generate failed';
                this.busy = false;
              },
            });
          },
          error: (e) => {
            this.error = e?.error?.detail?.message || 'Request failed';
            this.busy = false;
          },
        });
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Create failed';
        this.busy = false;
      },
    });
  }
}
