import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { StatsService } from '../../analytics/services/stats.service';
import { TracksService } from '../services/tracks.service';
import { GenresService } from '../services/genres.service';
import { ArtistsService } from '../services/artists.service';
import { PlaylistsService } from '../services/playlists.service';
import { AuthService } from '../../../core/services/auth.service';
import { HistoryService } from '../services/history.service';
import { FavoritesService } from '../services/favorites.service';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import {
  StatsSummary, TopTrack, GeneroPopularidad, HistoryEntry, PlaylistSummary, Track,
} from '../../../shared/models/api.models';
import { PlayableTrack } from '../../../shared/models/player.models';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule, RouterModule, HorizontalSectionComponent, MediaCardComponent,
    TrackRowComponent, KpiCardComponent, TranslatePipe,
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
  private auth = inject(AuthService);
  private favoritesSvc = inject(FavoritesService);
  player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);
  private i18n = inject(I18nService);

  greetingKey = computed(() => {
    this.i18n.tick();
    return this.i18n.greetingKey();
  });

  /** Clean track name for display (strips warehouse noise like " · #12345"). */
  cleanTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }

  /** Initials for artist avatars (minimalist, no real image needed). */
  initials(name?: string | null): string {
    return this.covers.initialsFor(name ?? '');
  }

  /** Collapse repeated titles in recently-played and cap to 8. */
  private dedupeHistory(entries: HistoryEntry[]): HistoryEntry[] {
    const seen = new Set<string>();
    const out: HistoryEntry[] = [];
    for (const e of entries) {
      const key = displayTrackTitle(e.nombre_track).toLowerCase().trim();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(e);
      if (out.length >= 8) break;
    }
    return out;
  }

  summaryLoading = signal(true);
  railsLoading = signal(true);
  hasError = signal(false);
  summary = signal<StatsSummary | null>(null);
  topTracks = signal<TopTrack[]>([]);
  discoverTracks = signal<Track[]>([]);
  genres = signal<GeneroPopularidad[]>([]);
  artists = signal<{ id: number; name: string }[]>([]);
  playlists = signal<PlaylistSummary[]>([]);
  history = signal<HistoryEntry[]>([]);
  rawHistory = signal<HistoryEntry[]>([]);
  favoritesCount = signal(0);
  growthLabels = signal<string[]>([]);
  growthValues = signal<number[]>([]);
  readonly heroStatSkels = [1, 2, 3, 4, 5];
  readonly kpiSkels = [1, 2, 3, 4, 5, 6, 7, 8];

  userName = computed(() => this.auth.getUser()?.username ?? 'demo');
  userPlan = computed(() => this.auth.getUser()?.plan ?? 'Free');

  listenStreak = computed(() => {
    const dates = new Set(
      this.rawHistory().map((e) => e.viewed_at?.slice(0, 10)).filter(Boolean),
    );
    if (!dates.size) return 0;
    let streak = 0;
    const d = new Date();
    for (;;) {
      const key = d.toISOString().slice(0, 10);
      if (!dates.has(key)) break;
      streak++;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  });

  listenMinutesToday = computed(() => {
    const today = new Date().toISOString().slice(0, 10);
    const n = this.rawHistory().filter((e) => e.viewed_at?.startsWith(today)).length;
    return Math.round(n * 3.5);
  });

  listenMinutesWeek = computed(() => {
    const weekAgo = Date.now() - 7 * 86_400_000;
    const n = this.rawHistory().filter((e) => new Date(e.viewed_at).getTime() >= weekAgo).length;
    return Math.round(n * 3.5);
  });

  /** Objetivo de tiempo semanal: 10 h = 600 min. */
  weeklyTimePct = computed(() => Math.min(100, Math.round((this.listenMinutesWeek() / 600) * 100)));

  /** Formatea minutos como "8 h 25 min" o "25 min". */
  formatDuration(min: number): string {
    const h = Math.floor(min / 60);
    const m = min % 60;
    if (h > 0) return `${h} h ${m} min`;
    return `${m} min`;
  }

  weeklyTimeLabel = computed(() => this.formatDuration(this.listenMinutesWeek()));

  /** Tendencias naturales y estables por KPI (no hay datos semana-a-semana reales). */
  private static KPI_TRENDS: Record<string, { text: string; positive: boolean }> = {
    tracks: { text: '+6%', positive: true },
    artists: { text: '+8%', positive: true },
    albums: { text: '+5%', positive: true },
    playlists: { text: '+3%', positive: true },
    streams: { text: '+9%', positive: true },
    favorites: { text: '+6%', positive: true },
    likes: { text: '+4%', positive: true },
  };

  kpiTrend(key: string): { text: string; positive: boolean } | null {
    return HomeComponent.KPI_TRENDS[key] ?? null;
  }

  weeklyDiscoverCount = computed(() => {
    const weekAgo = Date.now() - 7 * 86_400_000;
    const ids = new Set(
      this.rawHistory()
        .filter((e) => new Date(e.viewed_at).getTime() >= weekAgo)
        .map((e) => e.id_track),
    );
    return ids.size;
  });

  weeklyGoalPct = computed(() => Math.min(100, Math.round((this.weeklyDiscoverCount() / 100) * 100)));

  catalogGrowthTrend = computed(() => {
    const v = this.growthValues();
    if (v.length < 2) return null;
    const prev = v[v.length - 2];
    const cur = v[v.length - 1];
    if (!prev) return null;
    return Math.round(((cur - prev) / prev) * 100);
  });

  recommendationReason = computed(() => {
    const h = this.rawHistory()[0];
    if (!h?.nombre_artista) return '';
    return this.i18n.t('home.reco.because', { artist: h.nombre_artista });
  });

  /** Lista de artistas distintos del historial para variar el motivo por tarjeta. */
  private historyArtists = computed(() => {
    const seen = new Set<string>();
    const out: string[] = [];
    for (const e of this.rawHistory()) {
      const a = e.nombre_artista?.trim();
      if (!a || seen.has(a)) continue;
      seen.add(a);
      out.push(a);
    }
    return out;
  });

  recommendationReasonFor(index: number): string {
    const artists = this.historyArtists();
    if (!artists.length) return this.i18n.t('home.reco.becauseGeneric');
    const artist = artists[index % artists.length];
    return this.i18n.t('home.reco.because', { artist });
  }

  /** "Hecho para ti": rota el motivo para dar personalidad a cada tarjeta. */
  madeForYouReason(index: number): string {
    const artists = this.historyArtists();
    const genre = this.topGenre();
    const mode = index % 4;
    if (mode === 0 && artists.length) {
      return this.i18n.t('home.made.because', { artist: artists[index % artists.length] });
    }
    if (mode === 1 && genre) {
      return this.i18n.t('home.made.genre', { genre });
    }
    if (mode === 2) {
      return this.i18n.t('home.made.favorites');
    }
    if (artists.length) {
      return this.i18n.t('home.made.related', { artist: artists[(index + 1) % artists.length] });
    }
    return this.i18n.t('home.made.popular');
  }

  /** Compatibilidad determinista por track para "Recomendado para ti". */
  recoCompatibility(id: number): number {
    return 86 + (id % 14);
  }

  recoMeta(id: number): string {
    return this.i18n.t('home.reco.compat', { pct: this.recoCompatibility(id) });
  }

  recoBadge(index: number): string {
    const mode = index % 3;
    if (mode === 0) return this.i18n.t('home.reco.badgeNew');
    if (mode === 1) return this.i18n.t('home.reco.badgeSimilar');
    return this.i18n.t('home.reco.badgeMatch');
  }

  activityFeed = computed(() =>
    this.rawHistory().slice(0, 6).map((e) => ({
      ...e,
      rel: this.relativeTime(e.viewed_at),
      label: this.i18n.t('home.activity.listened', { title: this.cleanTitle(e.nombre_track) }),
    })),
  );

  hourlyBuckets = computed(() => {
    const buckets = Array(24).fill(0);
    for (const e of this.rawHistory()) {
      const h = new Date(e.viewed_at).getHours();
      if (!Number.isNaN(h)) buckets[h]++;
    }
    const max = Math.max(...buckets, 1);
    return buckets.map((v) => Math.round((v / max) * 100));
  });

  explorerLevel = computed(() => Math.min(5, Math.floor(this.rawHistory().length / 15) + 1));

  trendStr = computed(() => {
    const v = this.catalogGrowthTrend();
    if (v == null) return null;
    return { text: `${v >= 0 ? '+' : ''}${v}%`, positive: v >= 0 };
  });

  playlistBadge(index: number): string | undefined {
    if (index === 0) return this.i18n.t('home.badge.popular');
    if (index === 1) return this.i18n.t('home.badge.new');
    if (index === 2) return this.i18n.t('home.badge.editorsPick');
    return undefined;
  }

  trackProgress(id: number): number {
    return 25 + (id % 65);
  }

  trackDuration(id: number): string {
    const sec = 180 + (id % 120);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  genreBars = computed(() => {
    const top = this.genres().slice(0, 6);
    const max = Math.max(...top.map((g) => g.total_tracks ?? 0), 1);
    return top.map((g) => ({
      name: g.nombre_genero ?? '—',
      pct: Math.max(6, Math.round(((g.total_tracks ?? 0) / max) * 100)),
      tracks: g.total_tracks ?? 0,
    }));
  });

  hasHistoryData = computed(() => this.rawHistory().length > 0);

  peakHour = computed(() => {
    const b = this.hourlyBuckets();
    let idx = 0;
    let best = -1;
    b.forEach((v, i) => { if (v > best) { best = v; idx = i; } });
    return idx;
  });

  // "Recomendado" y "Descubrir" comparten el mismo fetch (página aleatoria del catálogo)
  // pero en tramos distintos para que nunca se repitan entre sí ni con topTracks.
  recoForYou = computed(() => this.discoverTracks().slice(0, 8));
  recoForYouPlayable = computed(() => this.recoForYou().map((t) => this.player.fromTrack(t)));

  discoverShown = computed(() => this.discoverTracks().slice(8));
  discoverShownPlayable = computed(() => this.discoverShown().map((t) => this.player.fromTrack(t)));

  madeForYou = computed(() => this.topTracks().slice(0, 8));
  // Distinct "next tier" so it doesn't mirror "Hecho para ti".
  trending = computed(() => {
    const all = this.topTracks();
    const next = all.slice(8, 18);
    return next.length >= 4 ? next : all.slice(0, 10);
  });

  topGenre = computed(() => this.genres()[0]?.nombre_genero?.trim() || null);
  topArtist = computed(() => this.artists()[0]?.name?.trim() || null);

  madeForYouPlayable = computed(() => this.madeForYou().map((t) => this.player.fromTopTrack(t)));
  trendingPlayable = computed(() => this.trending().map((t) => this.player.fromTopTrack(t)));
  discoverSubtitle = computed(() => {
    this.i18n.tick();
    const total = this.summary()?.total_tracks;
    if (!total) return '';
    return this.i18n.t('home.section.discoverSub', { total: this.fmt(total) });
  });

  initialLoadDone = computed(() => !this.summaryLoading() && !this.railsLoading());

  feedEmpty = computed(() =>
    this.initialLoadDone()
    && !this.history().length
    && !this.madeForYou().length
    && !this.trending().length
    && !this.discoverTracks().length
    && !this.artists().length
    && !this.playlists().length
    && !this.genres().length
    && !this.topTracks().length
  );

  sparkLine = computed(() => {
    const data = this.growthValues();
    if (!data.length) return '';
    const max = Math.max(...data, 1);
    return data.map((v, i) => `${i * (440 / Math.max(data.length - 1, 1))},${72 - (v / max) * 56}`).join(' ');
  });

  sparkArea = computed(() => {
    const data = this.growthValues();
    if (!data.length) return '';
    const line = this.sparkLine();
    const w = (data.length - 1) * (440 / Math.max(data.length - 1, 1));
    return `0,72 ${line} ${w},72`;
  });

  ngOnInit() {
    let railsPending = 5;
    const railDone = () => {
      if (--railsPending <= 0) this.railsLoading.set(false);
    };

    this.stats.getSummary().subscribe({
      next: (d) => {
        this.summary.set(d);
        if (d?.total_tracks) this.historySvc.pruneAbove(d.total_tracks);
        this.summaryLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.summaryLoading.set(false);
      },
    });
    this.stats.getTopTracks(24).subscribe({
      next: (d) => { this.topTracks.set(d ?? []); railDone(); },
      error: () => railDone(),
    });
    this.stats.getCatalogGrowth(12).subscribe({
      next: (pts) => {
        this.growthLabels.set(pts.map((p) => p.label));
        this.growthValues.set(pts.map((p) => p.total || p.added));
        railDone();
      },
      error: () => railDone(),
    });
    const discoverPage = (Math.floor(Date.now() / 86_400_000) % 120) + 5;
    this.tracksSvc.listTracks(discoverPage, 24).subscribe({
      next: (r) => { this.discoverTracks.set(r.items ?? []); railDone(); },
      error: () => railDone(),
    });
    this.genresSvc.getGenreStats(1, 8).subscribe({
      next: (r) => { this.genres.set(r.items ?? []); railDone(); },
      error: () => railDone(),
    });
    this.artistsSvc.listArtists(1, 8).subscribe({
      next: (r) => {
        this.artists.set((r.items ?? []).map((a) => ({ id: a.id_artista, name: a.nombre_artista })));
        railDone();
      },
      error: () => railDone(),
    });
    this.playlistsSvc.list().subscribe({
      next: (d) => { this.playlists.set((d ?? []).slice(0, 6)); railDone(); },
      error: () => railDone(),
    });
    this.historySvc.history$.subscribe((h) => {
      this.rawHistory.set(h);
      this.history.set(this.dedupeHistory(h));
    });
    this.historySvc.reload();
    this.favoritesSvc.favoriteIds$.subscribe((ids) => this.favoritesCount.set(ids.size));
  }

  cover(id: number | string): string {
    return this.covers.gradientFor(id);
  }

  historyPlayable(h: HistoryEntry): PlayableTrack {
    return {
      id: h.id_track,
      title: displayTrackTitle(h.nombre_track),
      artist: h.nombre_artista ?? '—',
      audioUrl: `/assets/audio/demo-${String((h.id_track % 8) + 1).padStart(2, '0')}.wav`,
      coverGradient: this.cover(h.id_track),
    };
  }

  trackPlayable(t: Track, artistName = '—'): PlayableTrack {
    return this.player.fromTrack(t, artistName);
  }

  barHeight(v: number): number {
    return Math.max(v, 4);
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

  energyMeta(energy?: number | null): string | undefined {
    if (energy == null) return undefined;
    const pct = energy <= 1 ? energy * 100 : energy;
    return this.i18n.t('home.energy', { value: Math.round(pct) });
  }

  relativeTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const min = Math.floor(diff / 60_000);
    if (min < 1) return this.i18n.t('home.time.justNow');
    if (min < 60) return this.i18n.t('home.time.minutes', { count: min });
    const hrs = Math.floor(min / 60);
    if (hrs < 24) return this.i18n.t('home.time.hours', { count: hrs });
    return this.i18n.t('home.time.days', { count: Math.floor(hrs / 24) });
  }

  trendTag(t: TopTrack, index: number): string | undefined {
    const pop = t.popularity ?? 0;
    if (index === 0) return this.i18n.t('home.badge.topGlobal');
    if (index === 1) return this.i18n.t('home.badge.rising');
    if (pop >= 96) return this.i18n.t('home.badge.hit');
    if (index < 4) return this.i18n.t('home.badge.trending');
    if (pop >= 90) return this.i18n.t('home.badge.popular');
    return this.i18n.t('home.badge.new');
  }

  artistOfDay = computed(() => this.artists()[0]?.name ?? null);

  artistAffinity(index: number): number {
    return Math.max(62, 98 - index * 7);
  }
}
