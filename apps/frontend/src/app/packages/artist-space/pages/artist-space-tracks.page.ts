import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-space-tracks',
  standalone: true,
  imports: [CommonModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.tracks.title' | t:lang()"
        [subtitle]="'artistSpace.tracks.subtitle' | t:lang()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (items().length === 0) {
        <app-enterprise-empty-state
          [title]="'artistSpace.tracks.emptyTitle' | t:lang()"
          [description]="'artistSpace.tracks.emptyBody' | t:lang()"
        />
      } @else {
        <ul class="track-list">
          @for (t of items(); track trackId(t)) {
            <li>{{ trackName(t) }}</li>
          }
        </ul>
        <p class="muted">{{ 'artistSpace.tracks.total' | t:lang() }}: {{ total() }}</p>
      }
    </div>
  `,
  styles: [
    `
      .track-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .track-list li {
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--vx-border, #3333);
      }
    `,
  ],
})
export class ArtistSpaceTracksPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<Record<string, unknown>[]>([]);
  readonly total = signal(0);

  ngOnInit(): void {
    this.load();
  }

  trackId(t: Record<string, unknown>): number {
    return Number(t['id_track'] ?? 0);
  }

  trackName(t: Record<string, unknown>): string {
    return String(t['nombre_track'] ?? '—');
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.loading.set(true);
    this.api.tracks(id).subscribe({
      next: (r) => {
        this.items.set((r.items || []) as Record<string, unknown>[]);
        this.total.set(r.total || 0);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.message || 'load_failed');
        this.loading.set(false);
      },
    });
  }
}
