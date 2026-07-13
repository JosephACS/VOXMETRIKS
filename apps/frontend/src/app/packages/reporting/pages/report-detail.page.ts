import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { ExecutiveReport } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-report-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="page">
      <p><a routerLink="/reports">← Reports</a></p>
      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (error) {
        <p class="error">{{ error }}</p>
      } @else if (report) {
        <h1>{{ report.title }}</h1>
        <p class="subtitle">Immutable academic snapshot — not a certified financial statement.</p>
        <p>
          Status: <span class="badge">{{ report.status }}</span>
        </p>
        <p>
          Period:
          {{ report.period_start || ('common.notAvailable' | t:lang()) }} → {{ report.period_end || ('common.notAvailable' | t:lang()) }}
        </p>
        <div class="actions">
          <button type="button" (click)="approve()" [disabled]="busy">Approve</button>
          <button type="button" (click)="publish()" [disabled]="busy">Publish</button>
          <button type="button" (click)="archive()" [disabled]="busy">Archive</button>
          <button type="button" (click)="exportCsv()" [disabled]="busy">{{ 'reporting.detail.exportCsv' | t:lang() }}</button>
        </div>

        @if (snapshotLoading) {
          <p>Loading snapshot…</p>
        } @else if (snapshot) {
          <section class="cs-card">
            <h2>Frozen snapshot</h2>
            <p class="muted">{{ snapshot.limitations || '' }}</p>
            <p>
              Unavailable sources:
              {{ snapshot.unavailable_sources_json || '[]' }}
            </p>
            @if (kpiRows.length) {
              <table class="data-table">
                <thead>
                  <tr><th>KPI</th><th>Value</th><th>Status</th></tr>
                </thead>
                <tbody>
                  @for (k of kpiRows; track k.code) {
                    <tr>
                      <td>{{ k.code }}</td>
                      <td>
                        @if (k.value == null) {
                          <em>{{ 'common.notAvailable' | t:lang() }}</em>
                        } @else {
                          {{ k.value }}
                        }
                      </td>
                      <td>{{ k.status || k.quality_status || '—' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            } @else {
              <p class="empty-state">No KPI rows in snapshot.</p>
            }
          </section>
        }

        @if (success) {
          <p class="success">{{ success }}</p>
        }
      }
    </div>
  `,
})
export class ReportDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private http = inject(HttpClient);

  orgId: number | null = null;
  report: ExecutiveReport | null = null;
  snapshot: {
    limitations?: string;
    unavailable_sources_json?: string;
    payload_json?: string;
  } | null = null;
  kpiRows: Array<{ code: string; value?: number | null; status?: string; quality_status?: string }> = [];
  loading = false;
  snapshotLoading = false;
  busy = false;
  error = '';
  success = '';
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
        this.loadSnapshot();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Denied or not found';
        this.loading = false;
      },
    });
  }

  loadSnapshot(): void {
    if (!this.orgId) return;
    this.snapshotLoading = true;
    this.http
      .get<{
        limitations?: string;
        unavailable_sources_json?: string;
        payload_json?: string;
      }>(`${environment.apiUrl}/reports/executive/${this.id}/snapshot`, {
        headers: { 'X-Organization-Id': String(this.orgId) },
      })
      .subscribe({
        next: (s) => {
          this.snapshot = s;
          try {
            const payload = JSON.parse(s.payload_json || '{}');
            this.kpiRows = Array.isArray(payload.kpis) ? payload.kpis : [];
          } catch {
            this.kpiRows = [];
          }
          this.snapshotLoading = false;
        },
        error: () => {
          this.snapshotLoading = false;
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
        this.success = 'Report approved.';
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
        this.success = 'Report published.';
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
        this.success = 'Report archived.';
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
        this.success = 'CSV downloaded (academic export).';
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Export failed';
      },
    });
  }
}
