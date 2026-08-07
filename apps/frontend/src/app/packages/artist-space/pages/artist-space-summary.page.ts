import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistSpaceSummary } from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-space-summary',
  standalone: true,
  imports: [CommonModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="displayName() || ('artistSpace.summary.title' | t:lang())"
        [subtitle]="'artistSpace.summary.subtitle' | t:lang()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (summary(); as s) {
        <div class="summary-grid">
          <app-enterprise-section-card [title]="'artistSpace.summary.team' | t:lang()">
            <p class="stat">{{ s.team_size }}</p>
          </app-enterprise-section-card>
          <app-enterprise-section-card [title]="'artistSpace.summary.tracks' | t:lang()">
            <p class="stat">{{ s.track_count }}</p>
          </app-enterprise-section-card>
          <app-enterprise-section-card [title]="'artistSpace.summary.pending' | t:lang()">
            <p class="stat">{{ s.pending_access_requests }}</p>
          </app-enterprise-section-card>
        </div>
      }
    </div>
  `,
  styles: [
    `
      .summary-grid {
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      }
      .stat {
        font-size: 1.75rem;
        font-weight: 600;
        margin: 0;
      }
    `,
  ],
})
export class ArtistSpaceSummaryPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly displayName = this.artistCtx.displayName;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly summary = signal<ArtistSpaceSummary | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) {
      this.error.set('no_artist');
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.api.summary(id).subscribe({
      next: (s) => {
        this.summary.set(s);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.message || 'load_failed');
        this.loading.set(false);
      },
    });
  }
}
