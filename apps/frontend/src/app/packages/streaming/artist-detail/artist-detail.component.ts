import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ArtistsService } from '../services/artists.service';
import { TracksService } from '../services/tracks.service';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { ArtistStats, Track } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { I18nService } from '../../../core/services/i18n.service';
import { translateSystemCode } from '../../../core/i18n/system-labels';
import { SmartHomeService } from '../../smart/services/smart-home.service';
import { SmartArtistItem } from '../../smart/models/smart-home.models';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { CoverArtService } from '../../../shared/services/cover-art.service';

@Component({
  selector: 'app-artist-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, TrackRowComponent, KpiCardComponent, TranslatePipe, DataSourceBadgeComponent, HorizontalSectionComponent, MediaCardComponent],
  templateUrl: './artist-detail.component.html',
  styleUrls: ['./artist-detail.component.css'],
})
export class ArtistDetailComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);
  private i18n = inject(I18nService);
  private destroyRef = inject(DestroyRef);
  private smartSvc = inject(SmartHomeService);
  private covers = inject(CoverArtService);
  player = inject(MusicPlayerService);

  stats = signal<ArtistStats | null>(null);
  tracks = signal<Track[]>([]);
  similarArtists = signal<SmartArtistItem[]>([]);
  trackTotal = signal(0);
  trackPage = signal(1);
  isLoading = signal(true);
  tracksLoading = signal(false);
  hasError = signal(false);
  partialError = signal('');

  readonly trackLimit = 50;

  displayName = computed(() => primaryArtistName(this.stats()?.nombre_artista));
  avatarInitial = computed(() => this.displayName().charAt(0).toUpperCase() || '?');
  avatarGradient = computed(() => {
    const id = this.stats()?.id_artista ?? 0;
    const hues = [145, 265, 200, 320, 180];
    const h = hues[id % hues.length];
    return `linear-gradient(135deg, hsl(${h}, 65%, 42%) 0%, hsl(${(h + 40) % 360}, 55%, 28%) 100%)`;
  });
  hasMoreTracks = computed(() => this.tracks().length < this.trackTotal());
  avgPopularity = computed(() => this.stats()?.promedio_popularidad ?? 0);

  constructor(
    private route: ActivatedRoute,
    private artistsSvc: ArtistsService,
    private tracksSvc: TracksService,
  ) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((pm) => {
        const id = Number(pm.get('id'));
        if (!id) return;
        this.trackPage.set(1);
        this.tracks.set([]);
        this.load(id);
      });
  }

  load(id: number) {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.partialError.set('');
    let pending = 2;
    let statsOk = false;
    let tracksOk = false;

    const done = () => {
      if (--pending > 0) return;
      this.isLoading.set(false);
      if (!statsOk && !tracksOk) this.hasError.set(true);
      else if (!statsOk) this.partialError.set(this.i18n.t('artistDetail.partialStats'));
    };

    this.artistsSvc.getArtistStats(id).subscribe({
      next: (s) => {
        this.stats.set(s);
        statsOk = true;
        this.loadSimilarArtists(id);
        done();
      },
      error: (err) => { console.error('[ArtistDetailComponent] getArtistStats failed', err); done(); },
    });
    this.fetchTracks(id, 1, true).then((ok) => { tracksOk = ok; done(); });
  }

  private fetchTracks(artistId: number, page: number, replace: boolean): Promise<boolean> {
    return new Promise((resolve) => {
      if (!replace) this.tracksLoading.set(true);
      this.tracksSvc.listTracks(page, this.trackLimit, undefined, undefined, artistId).subscribe({
        next: (r) => {
          const items = r.items ?? [];
          this.trackTotal.set(r.total ?? items.length);
          this.tracks.update((prev) => {
            if (replace) return items;
            const seen = new Set(prev.map((t) => t.id_track));
            return [...prev, ...items.filter((t) => !seen.has(t.id_track))];
          });
          this.trackPage.set(page);
          this.tracksLoading.set(false);
          resolve(true);
        },
        error: () => {
          this.tracksLoading.set(false);
          this.partialError.set(this.i18n.t('artistDetail.partialStats'));
          resolve(false);
        },
      });
    });
  }

  loadMoreTracks() {
    const id = this.stats()?.id_artista;
    if (!id || !this.hasMoreTracks() || this.tracksLoading()) return;
    this.fetchTracks(id, this.trackPage() + 1, false);
  }

  trackQueue = computed(() => this.tracks().map((t) => this.player.fromTrack(t)));

  playAll() {
    const queue = this.trackQueue();
    if (!queue.length) return;
    this.player.playTrack(queue[0], queue);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  artistCover(id: number): string {
    return this.covers.gradientFor(id);
  }

  similarArtistMeta(item: SmartArtistItem): string | undefined {
    this.i18n.lang();
    if (item.similarity == null) return undefined;
    return translateSystemCode('meta_similar', (k, p) => this.i18n.t(k, p), {
      pct: Math.round(item.similarity * 100),
    }) ?? undefined;
  }

  similarArtistName(item: SmartArtistItem): string {
    return primaryArtistName(item.nombre_artista);
  }

  private loadSimilarArtists(artistId: number) {
    this.similarArtists.set([]);
    this.smartSvc.getSimilarArtists(artistId).subscribe({
      next: (res) => this.similarArtists.set(res.similar ?? []),
      error: () => this.similarArtists.set([]),
    });
  }
}
