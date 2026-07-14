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
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-report-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise report-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/reports" class="back-link">{{ 'reporting.detail.back' | t:lang() }}</a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error && !report) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (report) {
          <app-enterprise-page-header
            [title]="report.title"
            [subtitle]="'reporting.detail.immutable' | t:lang()"
          >
            <app-enterprise-status-badge [status]="report.status" />
          </app-enterprise-page-header>

          <p class="muted">
            {{ 'common.period' | t:lang() }}:
            {{ report.period_start || ('common.notAvailable' | t:lang()) }} →
            {{ report.period_end || ('common.notAvailable' | t:lang()) }}
          </p>

          <app-enterprise-action-bar>
            <button type="button" class="btn btn--primary" (click)="approve()" [disabled]="busy">
              {{ 'reporting.detail.approve' | t:lang() }}
            </button>
            <button type="button" class="btn btn--secondary" (click)="publish()" [disabled]="busy">
              {{ 'reporting.detail.publish' | t:lang() }}
            </button>
            <button type="button" class="btn btn--ghost" (click)="archive()" [disabled]="busy">
              {{ 'reporting.detail.archive' | t:lang() }}
            </button>
            <button type="button" class="btn btn--secondary" (click)="exportCsv()" [disabled]="busy">
              {{ 'reporting.detail.exportCsv' | t:lang() }}
            </button>
          </app-enterprise-action-bar>

          @if (snapshotLoading) {
            <app-enterprise-loading-skeleton [rows]="3" />
          } @else if (snapshot) {
            <app-enterprise-section-card [title]="'reporting.detail.snapshot' | t:lang()">
              <p class="muted">{{ snapshot.limitations || '' }}</p>
              <p>
                {{ 'reporting.detail.unavailableSources' | t:lang() }}:
                {{ snapshot.unavailable_sources_json || '[]' }}
              </p>
              @if (kpiRows.length) {
                <app-enterprise-data-table>
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>{{ 'reporting.detail.kpi' | t:lang() }}</th>
                        <th>{{ 'reporting.detail.value' | t:lang() }}</th>
                        <th>{{ 'common.status' | t:lang() }}</th>
                      </tr>
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
                </app-enterprise-data-table>
              } @else {
                <p class="muted">{{ 'reporting.detail.noKpis' | t:lang() }}</p>
              }
            </app-enterprise-section-card>
          }

          @if (success) {
            <p class="success">{{ success }}</p>
          }
          @if (error) {
            <app-enterprise-error-state [message]="error" />
          }
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
    this.orgId = this.orgCtx.organizationId();
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
    else this.error = this.i18n.t('common.orgRequiredContext');
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = '';
    this.api.getExecutive(this.orgId, this.id).subscribe({
      next: (r) => {
        this.report = r;
        this.loading = false;
        this.loadSnapshot();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
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
        this.success = this.i18n.t('reporting.detail.approved');
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
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
        this.success = this.i18n.t('reporting.detail.published');
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
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
        this.success = this.i18n.t('reporting.detail.archived');
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
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
        this.success = this.i18n.t('reporting.detail.exportDone');
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
      },
    });
  }
}
