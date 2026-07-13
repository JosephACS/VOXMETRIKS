import {
  Component, Input, OnChanges, OnDestroy, SimpleChanges, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, of, Subscription } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';

/**
 * Spotify-style playlist/album cover mosaic from track cover URLs.
 */
@Component({
  selector: 'app-cover-mosaic',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="mosaic"
      [class.n0]="urls().length === 0"
      [class.n1]="urls().length === 1"
      [class.n2]="urls().length === 2"
      [class.n3]="urls().length === 3"
      [class.n4]="urls().length >= 4"
      [style.background]="fallbackGradient"
    >
      @if (loading()) {
        <div class="mosaic-skel" aria-hidden="true"></div>
      } @else if (urls().length === 0) {
        <div class="mosaic-empty">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
            <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
          </svg>
          @if (label) {
            <span class="mosaic-label">{{ label }}</span>
          }
        </div>
      } @else {
        @for (u of displayUrls; track $index) {
          <div class="tile" [style.background-image]="'url(' + u + ')'"></div>
        }
      }
    </div>
  `,
  styles: [`
    :host { display: block; width: 100%; height: 100%; }
    .mosaic {
      position: relative;
      width: 100%;
      height: 100%;
      border-radius: inherit;
      overflow: hidden;
      display: grid;
      background: #2a2a2a;
    }
    .mosaic.n1 { grid-template-columns: 1fr; grid-template-rows: 1fr; }
    .mosaic.n2 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr; }
    .mosaic.n3 {
      grid-template-columns: 1.2fr 0.8fr;
      grid-template-rows: 1fr 1fr;
    }
    .mosaic.n3 .tile:first-child { grid-row: 1 / span 2; }
    .mosaic.n4 {
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr 1fr;
    }
    .tile {
      background-size: cover;
      background-position: center;
      min-height: 0;
    }
    .mosaic-empty {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      color: rgba(255,255,255,0.55);
    }
    .mosaic-label {
      font-size: 0.7rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      opacity: 0.8;
    }
    .mosaic-skel {
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, rgba(255,255,255,0.04), rgba(255,255,255,0.1), rgba(255,255,255,0.04));
      background-size: 200% 100%;
      animation: mosaicShimmer 1.2s ease-in-out infinite;
    }
    @keyframes mosaicShimmer {
      0% { background-position: 100% 0; }
      100% { background-position: -100% 0; }
    }
  `],
})
export class CoverMosaicComponent implements OnChanges, OnDestroy {
  private readonly covers = inject(CoverArtService);
  private readonly coverSvc = inject(TrackCoverService);
  private sub: Subscription | null = null;

  @Input() trackIds: number[] = [];
  @Input() seed: string | number = 'playlist';
  @Input() label?: string;

  loading = signal(true);
  urls = signal<string[]>([]);

  get fallbackGradient(): string {
    return this.covers.gradientFor(this.seed);
  }

  get displayUrls(): string[] {
    const u = this.urls();
    return u.length >= 4 ? u.slice(0, 4) : u;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['trackIds']) this.load();
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  private load(): void {
    this.sub?.unsubscribe();
    const ids = (this.trackIds || []).filter((id) => id > 0).slice(0, 4);
    if (!ids.length) {
      this.urls.set([]);
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.sub = forkJoin(
      ids.map((id) =>
        this.coverSvc.trackCover$(id).pipe(
          map((url) => url),
          catchError(() => of(null)),
        ),
      ),
    ).subscribe((results) => {
      this.urls.set(results.filter((u): u is string => !!u));
      this.loading.set(false);
    });
  }
}
