import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-space-releases',
  standalone: true,
  imports: [CommonModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.releases.title' | t:lang()"
        [subtitle]="'artistSpace.releases.subtitle' | t:lang()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (items().length === 0) {
        <app-enterprise-empty-state
          [title]="'artistSpace.releases.emptyTitle' | t:lang()"
          [description]="'artistSpace.releases.emptyBody' | t:lang()"
        />
      } @else {
        <ul class="rel-list">
          @for (r of items(); track releaseId(r)) {
            <li>
              <strong>{{ releaseTitle(r) }}</strong>
              <span class="muted"> — {{ releaseStatus(r) }}</span>
            </li>
          }
        </ul>
      }
    </div>
  `,
  styles: [
    `
      .rel-list {
        list-style: none;
        padding: 0;
      }
      .rel-list li {
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--vx-border, #3333);
      }
    `,
  ],
})
export class ArtistSpaceReleasesPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<Record<string, unknown>[]>([]);

  ngOnInit(): void {
    this.load();
  }

  releaseId(r: Record<string, unknown>): number {
    return Number(r['id'] ?? 0);
  }
  releaseTitle(r: Record<string, unknown>): string {
    return String(r['title'] ?? '—');
  }
  releaseStatus(r: Record<string, unknown>): string {
    return String(r['status'] ?? '');
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.loading.set(true);
    this.api.releases(id).subscribe({
      next: (r) => {
        this.items.set((r.items || []) as Record<string, unknown>[]);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.message || 'load_failed');
        this.loading.set(false);
      },
    });
  }
}
