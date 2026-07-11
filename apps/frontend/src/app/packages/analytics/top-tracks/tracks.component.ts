import {
  AfterViewInit,
  Component,
  DestroyRef,
  ElementRef,
  OnDestroy,
  OnInit,
  computed,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, map, of, retry, timer } from 'rxjs';
import { EnterpriseTracksService } from '../../../core/services/tracks.service';
import { StatsService } from '../services/stats.service';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TopTrack as EnterpriseTopTrack } from '../../../core/models/enterprise-api.models';
import { TopTrack as StatsTopTrack } from '../../../shared/models/api.models';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';

export type TrackCard = EnterpriseTopTrack & { id_artista?: number; energy?: number; danceability?: number };

const PAGE_SIZE = 20;

@Component({
  selector: 'app-tracks-feature',
  standalone: true,
  imports: [MediaCardComponent, EmptyStateComponent],
  templateUrl: './tracks.component.html',
  styleUrl: './tracks.component.scss',
})
export class TracksFeatureComponent implements OnInit, AfterViewInit, OnDestroy {
  private readonly tracks = inject(EnterpriseTracksService);
  private readonly stats = inject(StatsService);
  readonly player = inject(MusicPlayerService);
  private readonly covers = inject(CoverArtService);
  private readonly destroyRef = inject(DestroyRef);

  private readonly sentinel = viewChild<ElementRef<HTMLElement>>('sentinel');
  private observer: IntersectionObserver | null = null;
  private scrollRootEl: HTMLElement | null = null;
  private scrollHandler: (() => void) | null = null;
  private useClientPaging = false;
  private clientPool: TrackCard[] = [];

  readonly loading = signal(true);
  readonly loadingMore = signal(false);
  readonly loadError = signal<string | null>(null);
  readonly allTracks = signal<TrackCard[]>([]);
  readonly serverTotal = signal(0);
  readonly currentPage = signal(0);

  readonly hasMore = computed(() => {
    const total = this.serverTotal();
    const loaded = this.allTracks().length;
    return total > 0 ? loaded < total : false;
  });

  readonly topTracksPlayable = computed(() =>
    this.allTracks().map((t) => this.player.fromTopTrack(t)),
  );

  constructor() {
    effect(() => {
      void this.allTracks().length;
      void this.hasMore();
      queueMicrotask(() => this.setupInfiniteScroll());
    });
  }

  ngOnInit(): void {
    this.loadNextPage();
  }

  ngAfterViewInit(): void {
    this.bindScrollRoot();
    this.setupInfiniteScroll();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    if (this.scrollRootEl && this.scrollHandler) {
      this.scrollRootEl.removeEventListener('scroll', this.scrollHandler);
    }
  }

  cleanTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }

  trackMeta(t: TrackCard): string {
    if (t.total_streams != null) {
      return `${t.total_streams.toLocaleString()} streams`;
    }
    if (t.engagement_score != null) {
      return `Engagement ${t.engagement_score}`;
    }
    if (t.popularity != null) {
      return `Pop. ${t.popularity}`;
    }
    return 'No disponible';
  }

  cover(trackId: number): string {
    return this.covers.gradientFor(String(trackId));
  }

  loadNextPage(): void {
    if (this.loadingMore() || (!this.hasMore() && this.currentPage() > 0)) return;

    if (this.useClientPaging) {
      this.loadMoreFromClientPool();
      return;
    }

    const nextPage = this.currentPage() + 1;
    if (nextPage === 1) this.loading.set(true);
    else this.loadingMore.set(true);

    this.tracks
      .getTopTracksPage(nextPage, PAGE_SIZE)
      .pipe(
        retry({ count: 2, delay: () => timer(600) }),
        catchError(() => this.bootstrapClientPool()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (res) => {
          if (this.useClientPaging) {
            this.loading.set(false);
            this.loadingMore.set(false);
            if (this.allTracks().length === 0 && this.clientPool.length) {
              this.loadMoreFromClientPool();
            }
            return;
          }
          const items = res.items as TrackCard[];
          this.serverTotal.set(res.total);
          this.currentPage.set(nextPage);
          this.allTracks.update((list) => {
            const seen = new Set(list.map((t) => t.id_track));
            const fresh = items.filter((t) => !seen.has(t.id_track));
            return [...list, ...fresh];
          });
          this.loadError.set(this.allTracks().length ? null : 'No hay canciones destacadas en el warehouse.');
          this.loading.set(false);
          this.loadingMore.set(false);
        },
        error: (err: Error) => {
          this.loadError.set(err.message);
          this.loading.set(false);
          this.loadingMore.set(false);
        },
      });
  }

  private bootstrapClientPool() {
    return this.stats.getTopTracks(100).pipe(
      map((rows) => {
        this.useClientPaging = true;
        this.clientPool = rows.map((r) => this.fromStatsTrack(r));
        this.serverTotal.set(this.clientPool.length);
        this.currentPage.set(0);
        return { items: [] as EnterpriseTopTrack[], total: this.clientPool.length };
      }),
      catchError(() => of({ items: [] as EnterpriseTopTrack[], total: 0 })),
    );
  }

  private loadMoreFromClientPool(): void {
    if (this.loadingMore() || !this.hasMore()) return;
    this.loadingMore.set(true);
    const start = this.allTracks().length;
    const chunk = this.clientPool.slice(start, start + PAGE_SIZE);
    this.allTracks.update((list) => {
      const seen = new Set(list.map((t) => t.id_track));
      const fresh = chunk.filter((t) => !seen.has(t.id_track));
      return [...list, ...fresh];
    });
    this.currentPage.update((p) => p + 1);
    this.loading.set(false);
    this.loadingMore.set(false);
  }

  private bindScrollRoot(): void {
    const el =
      this.sentinel()?.nativeElement.closest('.page-content') ??
      document.querySelector('.page-content');
    if (!(el instanceof HTMLElement) || el === this.scrollRootEl) return;

    if (this.scrollRootEl && this.scrollHandler) {
      this.scrollRootEl.removeEventListener('scroll', this.scrollHandler);
    }
    this.scrollRootEl = el;
    this.scrollHandler = () => {
      if (!this.hasMore() || this.loadingMore() || this.loading()) return;
      const { scrollTop, scrollHeight, clientHeight } = el;
      if (scrollTop + clientHeight >= scrollHeight - 320) {
        this.loadNextPage();
      }
    };
    el.addEventListener('scroll', this.scrollHandler, { passive: true });
  }

  private setupInfiniteScroll(): void {
    this.bindScrollRoot();
    this.observer?.disconnect();
    const el = this.sentinel()?.nativeElement;
    if (!el || typeof IntersectionObserver === 'undefined') return;

    const root = this.scrollRootEl ?? undefined;
    this.observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) this.loadNextPage();
      },
      { root: root ?? null, rootMargin: '320px', threshold: 0 },
    );
    this.observer.observe(el);

    if (this.useClientPaging && this.currentPage() === 0 && this.clientPool.length) {
      this.loadMoreFromClientPool();
    }
  }

  private fromStatsTrack(row: StatsTopTrack): TrackCard {
    return {
      id_track: row.id_track,
      nombre_track: row.nombre_track ?? '',
      nombre_artista: row.nombre_artista ?? '—',
      popularity: row.popularity ?? 0,
      total_streams: row.total_streams ?? null,
      engagement_score: row.engagement_score ?? null,
      id_artista: row.id_artista,
      energy: row.energy ?? undefined,
      danceability: row.danceability ?? undefined,
    };
  }
}
