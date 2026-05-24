import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { StatsService } from '../../analytics/services/stats.service';
import { TracksService } from '../services/tracks.service';
import { GenresService } from '../services/genres.service';
import { ArtistsService } from '../services/artists.service';
import { PlaylistsService } from '../services/playlists.service';
import { HistoryService } from '../services/history.service';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import {
  StatsSummary, TopTrack, GeneroPopularidad, HistoryEntry, PlaylistSummary, Track,
} from '../../../shared/models/api.models';
import { PlayableTrack } from '../../../shared/models/player.models';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule, RouterModule, HorizontalSectionComponent, MediaCardComponent,
    TrackRowComponent, KpiCardComponent,
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  private stats = inject(StatsService);
  private tracksSvc = inject(TracksService);
  private genresSvc = inject(GenresService);
  private artistsSvc = inject(ArtistsService);
  private playlistsSvc = inject(PlaylistsService);
  private historySvc = inject(HistoryService);
  player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);

  isLoading = signal(true);
  summary = signal<StatsSummary | null>(null);
  topTracks = signal<TopTrack[]>([]);
  recentTracks = signal<Track[]>([]);
  genres = signal<GeneroPopularidad[]>([]);
  artists = signal<{ id: number; name: string }[]>([]);
  playlists = signal<PlaylistSummary[]>([]);
  history = signal<HistoryEntry[]>([]);
  growthLabels = signal<string[]>([]);
  growthValues = signal<number[]>([]);

  madeForYou = computed(() => this.topTracks().slice(0, 8));
  trending = computed(() => this.topTracks().slice(0, 10));

  madeForYouPlayable = computed(() => this.madeForYou().map((t) => this.player.fromTopTrack(t)));
  trendingPlayable = computed(() => this.trending().map((t) => this.player.fromTopTrack(t)));

  ngOnInit() {
    let pending = 6;
    const done = () => { if (--pending <= 0) this.isLoading.set(false); };

    this.stats.getSummary().subscribe({
      next: (d) => { this.summary.set(d); done(); },
      error: () => done(),
    });
    this.stats.getTopTracks(12).subscribe({
      next: (d) => { this.topTracks.set(d ?? []); done(); },
      error: () => done(),
    });
    this.stats.getCatalogGrowth(12).subscribe({
      next: (pts) => {
        this.growthLabels.set(pts.map((p) => p.label));
        this.growthValues.set(pts.map((p) => p.total || p.added));
        done();
      },
      error: () => done(),
    });
    this.tracksSvc.listTracks(1, 12).subscribe({
      next: (r) => { this.recentTracks.set(r.items ?? []); done(); },
      error: () => done(),
    });
    this.genresSvc.getGenreStats(8).subscribe({
      next: (d) => { this.genres.set(d ?? []); done(); },
      error: () => done(),
    });
    this.artistsSvc.listArtists(1, 8).subscribe({
      next: (r) => {
        this.artists.set((r.items ?? []).map((a) => ({ id: a.id_artista, name: a.nombre_artista })));
        done();
      },
      error: () => done(),
    });
    this.playlistsSvc.list().subscribe({
      next: (d) => { this.playlists.set((d ?? []).slice(0, 6)); done(); },
      error: () => done(),
    });
    this.historySvc.history$.subscribe((h) => this.history.set(h.slice(0, 8)));
    this.historySvc.reload();
  }

  cover(id: number | string): string {
    return this.covers.gradientFor(id);
  }

  historyPlayable(h: HistoryEntry): PlayableTrack {
    return {
      id: h.id_track,
      title: h.nombre_track,
      artist: h.nombre_artista ?? '—',
      audioUrl: `/assets/audio/demo-${String((h.id_track % 8) + 1).padStart(2, '0')}.wav`,
      coverGradient: this.cover(h.id_track),
    };
  }

  trackPlayable(t: Track, artistName = '—'): PlayableTrack {
    return this.player.fromTrack(t, artistName);
  }

  sparkLine(): string {
    const data = this.growthValues();
    if (!data.length) return '';
    const max = Math.max(...data, 1);
    return data.map((v, i) => `${i * (440 / Math.max(data.length - 1, 1))},${90 - (v / max) * 70}`).join(' ');
  }

  sparkArea(): string {
    const data = this.growthValues();
    if (!data.length) return '';
    const line = this.sparkLine();
    const w = (data.length - 1) * (440 / Math.max(data.length - 1, 1));
    return `0,90 ${line} ${w},90`;
  }

  fmt(val?: number | null): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toLocaleString('es-ES');
  }

  popularityKpi(): number | null {
    const v = this.summary()?.promedio_popularidad;
    return v != null ? Math.round(v * 10) / 10 : null;
  }
}
