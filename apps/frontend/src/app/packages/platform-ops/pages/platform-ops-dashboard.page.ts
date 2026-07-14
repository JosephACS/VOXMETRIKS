import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import {
  BackupRecord,
  BackgroundJob,
  FeatureFlag,
  HealthStatus,
  ProviderConfig,
} from '../models/platform-ops.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-platform-ops-dashboard',
  standalone: true,
  imports: [CommonModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-ops-page">
      <app-enterprise-page-header
        [title]="'platformOps.dashboard.title' | t:lang()"
        [subtitle]="'platformOps.dashboard.subtitle' | t:lang()"
      />

      @if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      }

      @if (health) {
        <app-enterprise-section-card [title]="'platformOps.dashboard.health' | t:lang()">
          <p>
            <app-enterprise-status-badge [status]="health.status" />
            —
            {{
              health.labeled_academic
                ? ('platformOps.dashboard.healthMessageAcademic' | t:lang())
                : health.message
            }}
          </p>
          @if (health.labeled_academic) {
            <span class="badge">{{ 'platformOps.dashboard.academic' | t:lang() }}</span>
          }
        </app-enterprise-section-card>
      }

      <app-enterprise-section-card [title]="'platformOps.dashboard.providers' | t:lang()">
        @if (providers.length === 0) {
          <app-enterprise-empty-state
            [title]="'platformOps.dashboard.noProvidersTitle' | t:lang()"
            [description]="'platformOps.dashboard.noProvidersBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'platformOps.dashboard.code' | t:lang() }}</th>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'common.mock' | t:lang() }}</th>
                  <th>{{ 'platformOps.dashboard.secret' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (p of providers; track p.id) {
                  <tr>
                    <td>{{ p.provider_code }}</td>
                    <td>{{ p.display_name }}</td>
                    <td>
                      {{ p.is_mock ? ('common.mock' | t:lang()) : ('common.notAvailable' | t:lang()) }}
                    </td>
                    <td>{{ p.secret_ref_redacted || ('common.notAvailable' | t:lang()) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      </app-enterprise-section-card>

      <app-enterprise-section-card [title]="'platformOps.dashboard.jobs' | t:lang()">
        @if (jobs.length === 0) {
          <app-enterprise-empty-state
            [title]="'platformOps.dashboard.noJobsTitle' | t:lang()"
            [description]="'platformOps.dashboard.noJobsBody' | t:lang()"
          />
        } @else {
          <ul class="ent-list">
            @for (j of jobs; track j.id) {
              <li>
                {{ j.job_code }} —
                <app-enterprise-status-badge [status]="j.status" />
              </li>
            }
          </ul>
        }
      </app-enterprise-section-card>

      <app-enterprise-section-card [title]="'platformOps.dashboard.flags' | t:lang()">
        @if (flags.length === 0) {
          <app-enterprise-empty-state
            [title]="'platformOps.dashboard.noFlagsTitle' | t:lang()"
            [description]="'platformOps.dashboard.noFlagsBody' | t:lang()"
          />
        } @else {
          <ul class="ent-list">
            @for (f of flags; track f.id) {
              <li>
                {{ f.flag_key }}:
                <app-enterprise-status-badge [status]="f.enabled ? 'active' : 'closed'" />
              </li>
            }
          </ul>
        }
      </app-enterprise-section-card>

      <app-enterprise-section-card [title]="'platformOps.dashboard.backups' | t:lang()">
        @if (backups.length === 0) {
          <app-enterprise-empty-state
            [title]="'platformOps.dashboard.noBackupsTitle' | t:lang()"
            [description]="'platformOps.dashboard.noBackupsBody' | t:lang()"
          />
        } @else {
          <ul class="ent-list">
            @for (b of backups; track b.id) {
              <li>
                {{ b.file_path }}
                @if (b.labeled_academic) {
                  ({{ 'platformOps.dashboard.academic' | t:lang() }})
                }
              </li>
            }
          </ul>
        }
      </app-enterprise-section-card>
    </div>
  `,
})
export class PlatformOpsDashboardPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(PlatformOpsApiService);

  health: HealthStatus | null = null;
  providers: ProviderConfig[] = [];
  jobs: BackgroundJob[] = [];
  flags: FeatureFlag[] = [];
  backups: BackupRecord[] = [];
  error: string | null = null;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.api.getHealth().subscribe({
      next: (h) => {
        this.health = h;
      },
      error: (e) => {
        this.error = e?.error?.message || this.i18n.t('platformOps.dashboard.healthFailed');
      },
    });
    this.api.listProviders().subscribe({ next: (p) => (this.providers = p) });
    this.api.listJobs().subscribe({ next: (j) => (this.jobs = j) });
    this.api.listFlags().subscribe({ next: (f) => (this.flags = f) });
    this.api.listBackups().subscribe({ next: (b) => (this.backups = b) });
  }
}
