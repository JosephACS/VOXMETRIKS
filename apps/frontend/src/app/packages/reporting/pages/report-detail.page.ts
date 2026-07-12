import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { ExecutiveReport } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-report-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page">
      <p><a routerLink="/reports">← Reports</a></p>
      @if (loading) { <p>Loading…</p> }
      @else if (error) { <p class="error">{{ error }}</p> }
      @else if (report) {
        <h1>{{ report.title }}</h1>
        <p>Status: {{ report.status }}</p>
        <p>Period: {{ report.period_start || '—' }} → {{ report.period_end || '—' }}</p>
        <div class="actions">
          <button type="button" (click)="approve()" [disabled]="busy">Approve</button>
          <button type="button" (click)="publish()" [disabled]="busy">Publish</button>
          <button type="button" (click)="archive()" [disabled]="busy">Archive</button>
          <button type="button" (click)="exportCsv()" [disabled]="busy">Export CSV</button>
        </div>
      }
    </div>
  `,
})
export class ReportDetailPage implements OnInit {
  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);

  orgId: number | null = null;
  report: ExecutiveReport | null = null;
  loading = false;
  busy = false;
  error = '';
  id = 0;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
    else this.error = 'Missing organization or report id';
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.api.getExecutive(this.orgId, this.id).subscribe({
      next: (r) => {
        this.report = r;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Denied or not found';
        this.loading = false;
      },
    });
  }

  approve(): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.approve(this.orgId, this.id).subscribe({
      next: (r) => {
        this.report = r;
        this.busy = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Approve failed';
        this.busy = false;
      },
    });
  }

  publish(): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.publish(this.orgId, this.id).subscribe({
      next: (r) => {
        this.report = r;
        this.busy = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Publish failed';
        this.busy = false;
      },
    });
  }

  archive(): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.archive(this.orgId, this.id).subscribe({
      next: (r) => {
        this.report = r;
        this.busy = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Archive failed';
        this.busy = false;
      },
    });
  }

  exportCsv(): void {
    if (!this.orgId) return;
    this.api.exportCsv(this.orgId, this.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `executive-report-${this.id}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Export failed';
      },
    });
  }
}
