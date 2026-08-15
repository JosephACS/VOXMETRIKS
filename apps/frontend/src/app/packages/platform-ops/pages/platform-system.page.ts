import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
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

/**
 * Spec 055 — advanced system diagnostics (providers/jobs/flags/backups).
 * Simulated behavior is labeled honestly; not the default Platform Ops hub.
 */
@Component({
  selector: 'app-platform-system-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-ops-page" data-testid="platform-ops-system">
      <a routerLink="/platform-ops" class="back-link">{{ 'platformOps.system.back' | t: lang() }}</a>
      <app-enterprise-page-header
        [title]="'platformOps.system.title' | t: lang()"
        [subtitle]="'platformOps.system.subtitle' | t: lang()"
      />

      <p class="sim-banner" role="note">{{ 'platformOps.system.simulationBanner' | t: lang() }}</p>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else {
        @if (health(); as h) {
          <app-enterprise-section-card [title]="'platformOps.system.health' | t: lang()">
            <p>
              <app-enterprise-status-badge [status]="h.status" />
              —
              {{
                h.labeled_academic
                  ? ('platformOps.system.healthMessageSimulated' | t: lang())
                  : h.message
              }}
            </p>
            @if (h.labeled_academic) {
              <span class="badge">{{ 'platformOps.system.simulated' | t: lang() }}</span>
            }
          </app-enterprise-section-card>
        }

        <app-enterprise-section-card [title]="'platformOps.system.providers' | t: lang()">
          @if (providers().length === 0) {
            <app-enterprise-empty-state
              [title]="'platformOps.system.noProvidersTitle' | t: lang()"
              [description]="'platformOps.system.noProvidersBody' | t: lang()"
            />
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.name' | t: lang() }}</th>
                    <th>{{ 'platformOps.system.code' | t: lang() }}</th>
                    <th>{{ 'common.mock' | t: lang() }}</th>
                    <th>{{ 'platformOps.system.secret' | t: lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (p of providers(); track p.id) {
                    <tr>
                      <td>{{ p.display_name }}</td>
                      <td class="mono ref">{{ p.provider_code }}</td>
                      <td>
                        {{
                          p.is_mock
                            ? ('platformOps.system.simulated' | t: lang())
                            : ('common.notAvailable' | t: lang())
                        }}
                      </td>
                      <td class="ref">{{ p.secret_ref_redacted || ('common.notAvailable' | t: lang()) }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'platformOps.system.jobs' | t: lang()">
          @if (jobs().length === 0) {
            <app-enterprise-empty-state
              [title]="'platformOps.system.noJobsTitle' | t: lang()"
              [description]="'platformOps.system.noJobsBody' | t: lang()"
            />
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.name' | t: lang() }}</th>
                    <th>{{ 'platformOps.system.code' | t: lang() }}</th>
                    <th>{{ 'common.status' | t: lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (j of jobs(); track j.id) {
                    <tr>
                      <td>{{ j.display_name }}</td>
                      <td class="mono ref">{{ j.job_code }}</td>
                      <td><app-enterprise-status-badge [status]="j.status" /></td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'platformOps.system.flags' | t: lang()">
          @if (flags().length === 0) {
            <app-enterprise-empty-state
              [title]="'platformOps.system.noFlagsTitle' | t: lang()"
              [description]="'platformOps.system.noFlagsBody' | t: lang()"
            />
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'platformOps.system.code' | t: lang() }}</th>
                    <th>{{ 'common.status' | t: lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (f of flags(); track f.id) {
                    <tr>
                      <td class="mono">{{ f.flag_key }}</td>
                      <td>
                        <app-enterprise-status-badge [status]="f.enabled ? 'active' : 'closed'" />
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'platformOps.system.backups' | t: lang()">
          @if (backups().length === 0) {
            <app-enterprise-empty-state
              [title]="'platformOps.system.noBackupsTitle' | t: lang()"
              [description]="'platformOps.system.noBackupsBody' | t: lang()"
            />
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'platformOps.system.backupType' | t: lang() }}</th>
                    <th>{{ 'common.status' | t: lang() }}</th>
                    <th>{{ 'platformOps.system.simulated' | t: lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (b of backups(); track b.id) {
                    <tr>
                      <td>{{ b.backup_type }}</td>
                      <td><app-enterprise-status-badge [status]="b.status" /></td>
                      <td>
                        @if (b.labeled_academic) {
                          <span class="badge">{{ 'platformOps.system.simulated' | t: lang() }}</span>
                        } @else {
                          {{ 'common.notAvailable' | t: lang() }}
                        }
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
  styles: `
    .back-link {
      display: inline-block;
      margin-bottom: 0.75rem;
      color: rgba(255, 255, 255, 0.7);
      text-decoration: none;
    }
    .sim-banner {
      margin: 0 0 1rem;
      padding: 0.65rem 0.9rem;
      border-radius: 8px;
      background: rgba(240, 195, 106, 0.12);
      border: 1px solid rgba(240, 195, 106, 0.35);
      color: #f0c36a;
      font-size: 0.88rem;
    }
    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.85rem;
    }
    .ref {
      opacity: 0.65;
      font-size: 0.85rem;
    }
    .badge {
      display: inline-block;
      margin-top: 0.35rem;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      background: rgba(240, 195, 106, 0.18);
      font-size: 0.75rem;
    }
  `,
})
export class PlatformSystemPage implements OnInit {
  private readonly api = inject(PlatformOpsApiService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly health = signal<HealthStatus | null>(null);
  readonly providers = signal<ProviderConfig[]>([]);
  readonly jobs = signal<BackgroundJob[]>([]);
  readonly flags = signal<FeatureFlag[]>([]);
  readonly backups = signal<BackupRecord[]>([]);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    let pending = 5;
    const done = () => {
      pending -= 1;
      if (pending <= 0) this.loading.set(false);
    };

    this.api.getHealth().subscribe({
      next: (h) => {
        this.health.set(h);
        done();
      },
      error: (e) => {
        this.error.set(
          e?.error?.message || this.i18n.t('platformOps.system.healthFailed'),
        );
        done();
      },
    });
    this.api.listProviders().subscribe({
      next: (p) => {
        this.providers.set(p || []);
        done();
      },
      error: () => done(),
    });
    this.api.listJobs().subscribe({
      next: (j) => {
        this.jobs.set(j || []);
        done();
      },
      error: () => done(),
    });
    this.api.listFlags().subscribe({
      next: (f) => {
        this.flags.set(f || []);
        done();
      },
      error: () => done(),
    });
    this.api.listBackups().subscribe({
      next: (b) => {
        this.backups.set(b || []);
        done();
      },
      error: () => done(),
    });
  }
}
