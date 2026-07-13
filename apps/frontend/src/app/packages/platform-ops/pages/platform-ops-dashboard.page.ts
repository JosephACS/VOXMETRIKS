import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import { BackupRecord, BackgroundJob, FeatureFlag, HealthStatus, ProviderConfig } from '../models/platform-ops.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-platform-ops-dashboard',
  standalone: true,
  imports: [CommonModule, TranslatePipe],
  template: `
    <div class="platform-ops-dashboard">
      <h1>{{ 'platformOps.dashboard.title' | t:lang() }}</h1>
      <p class="subtitle">Academic/local ops console — not production HA. Secrets redacted in UI.</p>

      @if (health) {
        <section class="health-card">
          <h2>Health</h2>
          <p><strong>{{ health.status }}</strong> — {{ health.message }}</p>
          @if (health.labeled_academic) { <span class="badge">ACADEMIC</span> }
        </section>
      }

      <section>
        <h2>Providers</h2>
        @if (providers.length === 0) { <p>{{ 'platformOps.dashboard.noProviders' | t:lang() }}</p> }
        @else {
          <table>
            <thead><tr><th>Code</th><th>Name</th><th>Mock</th><th>Secret</th></tr></thead>
            <tbody>
              @for (p of providers; track p.id) {
                <tr>
                  <td>{{ p.provider_code }}</td>
                  <td>{{ p.display_name }}</td>
                  <td>{{ p.is_mock ? 'MOCK' : '—' }}</td>
                  <td>{{ p.secret_ref_redacted || '—' }}</td>
                </tr>
              }
            </tbody>
          </table>
        }
      </section>

      <section>
        <h2>Jobs</h2>
        @if (jobs.length === 0) { <p>No jobs registered.</p> }
        @else {
          <ul>@for (j of jobs; track j.id) { <li>{{ j.job_code }} — {{ j.status }}</li> }</ul>
        }
      </section>

      <section>
        <h2>Feature Flags</h2>
        @if (flags.length === 0) { <p>No flags.</p> }
        @else {
          <ul>@for (f of flags; track f.id) { <li>{{ f.flag_key }}: {{ f.enabled ? 'ON' : 'OFF' }}</li> }</ul>
        }
      </section>

      <section>
        <h2>Backups</h2>
        @if (backups.length === 0) { <p>No backups.</p> }
        @else {
          <ul>@for (b of backups; track b.id) { <li>{{ b.file_path }} ({{ b.labeled_academic ? 'academic' : '—' }})</li> }</ul>
        }
      </section>

      @if (error) { <p class="error">{{ error }}</p> }
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

  ngOnInit(): void { this.load(); }

  load(): void {
    this.api.getHealth().subscribe({
      next: (h) => { this.health = h; },
      error: (e) => { this.error = e?.error?.message || 'Health check failed'; },
    });
    this.api.listProviders().subscribe({ next: (p) => { this.providers = p; } });
    this.api.listJobs().subscribe({ next: (j) => { this.jobs = j; } });
    this.api.listFlags().subscribe({ next: (f) => { this.flags = f; } });
    this.api.listBackups().subscribe({ next: (b) => { this.backups = b; } });
  }
}
