import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { translateSystemCode } from '../../../core/i18n/system-labels';
import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { take } from 'rxjs';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { TracksService } from '../services/tracks.service';
import { HistoryService } from '../services/history.service';
import { TrackDetail } from '../../../shared/models/api.models';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { AddToPlaylistBtnComponent } from '../../../shared/components/add-to-playlist-btn/add-to-playlist-btn.component';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import { displayTrackTitle, displayTrackSubtitle } from '../../../shared/utils/track-display.util';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { SmartHomeService } from '../../smart/services/smart-home.service';
import { SmartTrackItem, smartItemToTrack } from '../../smart/models/smart-home.models';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { PlayerController } from '../../../playback-core/player.controller';

@Component({
  selector: 'app-track-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, AddToPlaylistBtnComponent, TranslatePipe, DataSourceBadgeComponent, HorizontalSectionComponent, MediaCardComponent],
  templateUrl: './track-detail.component.html',
  styleUrls: ['./track-detail.component.css'],
})
export class TrackDetailComponent implements OnInit {
  private readonly i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private iconRender = inject(IconRenderService);
  private coverArt = inject(CoverArtService);
  private coverSvc = inject(TrackCoverService);
  private destroyRef = inject(DestroyRef);
  private smartSvc = inject(SmartHomeService);
  readonly controller = inject(PlayerController);

  track = signal<TrackDetail | null>(null);
  similarTracks = signal<SmartTrackItem[]>([]);
  coverUrl = signal<string | null>(null);
  isLoading = signal(true);
  hasError = signal(false);

  featureBars = computed(() => {
    const t = this.track();
    if (!t) return [];
    return [
      { label: 'Energía', value: (t.energy ?? 0) * 100, color: '#1ed896' },
      { label: 'Bailabilidad', value: (t.danceability ?? 0) * 100, color: '#7c3aed' },
      { label: 'Valencia', value: (t.valence ?? 0) * 100, color: '#10b981' },
      { label: 'Acústica', value: (t.acousticness ?? 0) * 100, color: '#3b82f6' },
    ];
  });

  title = computed(() => displayTrackTitle(this.track()?.nombre_track));

  similarCatalog = computed(() => this.similarTracks().map(smartItemToTrack));
  similarPlayable = computed(() => this.similarCatalog().map((t) => this.controller.fromTrack(t)));

  sparkPoints = computed(() => {
    const t = this.track();
    if (!t) return '';
    const vals = [
      (t.energy ?? 0) * 80,
      (t.danceability ?? 0) * 70,
      (t.valence ?? 0) * 90,
      (t.acousticness ?? 0) * 60,
      (t.speechiness ?? 0) * 50,
      (t.instrumentalness ?? 0) * 40,
      (t.liveness ?? 0) * 55,
    ];
    return vals.map((v, i) => `${i * 40 + 10},${90 - v}`).join(' ');
  });

  constructor(
    private route: ActivatedRoute,
    private tracksSvc: TracksService,
    private history: HistoryService,
    private player: MusicPlayerService,
  ) {}

  ngOnInit() {
    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((pm) => {
        const id = Number(pm.get('id'));
        if (!id) return;
        this.load(id);
      });
  }

  load(id: number) {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.coverUrl.set(null);
    this.tracksSvc.getTrackDetail(id).subscribe({
      next: (d) => {
        this.track.set(d);
        this.isLoading.set(false);
        this.history.add({
          id_track: d.id_track,
          nombre_track: d.nombre_track ?? 'Track',
          nombre_artista: d.nombre_artista,
        });
        this.coverSvc.cover$(d.id_track)
          .pipe(take(1))
          .subscribe((url) => {
            if (this.track()?.id_track === d.id_track) this.coverUrl.set(url);
          });
        this.loadSimilar(d.id_track);
      },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  formatDuration(ms?: number): string {
    if (!ms) return '—';
    const m = Math.floor(ms / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  playTrack() {
    const t = this.track();
    if (!t) return;
    const artist = t.nombre_artista?.trim()
      ? primaryArtistName(t.nombre_artista)
      : '—';
    this.player.playTrack({
      id: t.id_track,
      title: displayTrackTitle(t.nombre_track),
      artist: displayTrackSubtitle(artist, t.nombre_genero, t.id_track),
      durationMs: t.duration_ms,
      audioUrl: '',
      coverGradient: this.coverArt.gradientFor(t.id_track),
      explicit: t.explicit,
    });
  }

  coverGradient(): string {
    const t = this.track();
    return this.coverArt.gradientFor(t?.id_track ?? 0);
  }

  coverFor(id: number): string {
    return this.coverArt.gradientFor(id);
  }

  similarMeta(item: SmartTrackItem): string | undefined {
    this.i18n.lang();
    if (item.similarity == null) return undefined;
    return translateSystemCode('meta_similar', (k, p) => this.i18n.t(k, p), {
      pct: Math.round(item.similarity * 100),
    }) ?? undefined;
  }

  private loadSimilar(trackId: number) {
    this.similarTracks.set([]);
    this.smartSvc.getSimilarTracks(trackId).subscribe({
      next: (res) => this.similarTracks.set(res.similar ?? []),
      error: () => this.similarTracks.set([]),
    });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
