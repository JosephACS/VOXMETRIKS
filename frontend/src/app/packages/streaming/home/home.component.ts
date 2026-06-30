import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DashboardService } from '../services/dashboard.service';
import { AuthService } from '../../../core/services/auth.service';
import { HistoryService } from '../services/history.service';
import { FavoritesService } from '../services/favorites.service';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import {
  StatsSummary, TopTrack, GeneroPopularidad, HistoryEntry, PlaylistSummary, Track,
} from '../../../shared/models/api.models';
import { PlayableTrack } from '../../../shared/models/player.models';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import {
  catalogGrowthTrend,
  dedupeHistory,
  genreBars,
  historyArtists,
  hourlyBuckets,
  listenMinutesToday,
  listenMinutesWeek,
  listenStreak,
  peakHourIndex,
  sparkArea,
  sparkLine,
  weeklyDiscoverCount,
} from './home-metrics.util';
import {
  artistAffinityPct,
  fmtNumber,
  formatDurationMin,
  recoCompatibilityPct,
  trackDurationLabel,
  trackProgressPct,
} from './home-format.util';
import { HomeHeroComponent } from './widgets/home-hero.component';
import { HomeAnalyticsBandComponent } from './widgets/home-analytics-band.component';
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule, RouterModule, HorizontalSectionComponent, MediaCardComponent,
    TrackRowComponent, TranslatePipe, HomeHeroComponent, HomeAnalyticsBandComponent,
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  private dashboardSvc = inject(DashboardService);
  private historySvc = inject(HistoryService);
  private auth = inject(AuthService);
  private favoritesSvc = inject(FavoritesService);
  private destroyRef = inject(DestroyRef);
  player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);
  private trackCover = inject(TrackCoverService);
  private i18n = inject(I18nService);
  /** Resolved real cover URLs per track id (same source the player uses). */
  private coverUrls = signal<Record<number, string>>({});
  readonly lang = this.i18n.lang;
  greetingKey = computed(() => {
    this.i18n.lang();
    return this.i18n.greetingKey();
  });
  cleanTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }
  initials(name?: string | null): string {
    return this.covers.initialsFor(name ?? '');
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
  listenStreak = computed(() => listenStreak(this.rawHistory()));
  listenMinutesToday = computed(() => listenMinutesToday(this.rawHistory()));
  listenMinutesWeek = computed(() => listenMinutesWeek(this.rawHistory()));
  weeklyTimePct = computed(() => Math.min(100, Math.round((this.listenMinutesWeek() / 600) * 100)));
  weeklyTimeLabel = computed(() => formatDurationMin(this.listenMinutesWeek()));
  weeklyDiscoverCount = computed(() => weeklyDiscoverCount(this.rawHistory()));
  weeklyGoalPct = computed(() => Math.min(100, Math.round((this.weeklyDiscoverCount() / 100) * 100)));
  catalogGrowthTrend = computed(() => catalogGrowthTrend(this.growthValues()));
  private historyArtists = computed(() => historyArtists(this.rawHistory()));
  recommendationReasonFor(index: number): string {
    const artists = this.historyArtists();
    if (!artists.length) return this.i18n.t('home.reco.becauseGeneric');
    return this.i18n.t('home.reco.because', { artist: artists[index % artists.length] });
  }
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
  recoMeta(id: number): string {
    return this.i18n.t('home.reco.compat', { pct: recoCompatibilityPct(id) });
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
  hourlyBuckets = computed(() => hourlyBuckets(this.rawHistory()));
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
  trackProgress = trackProgressPct;
  trackDuration = trackDurationLabel;
  genreBars = computed(() => genreBars(this.genres()));
  hasHistoryData = computed(() => this.rawHistory().length > 0);
  peakHour = computed(() => peakHourIndex(this.hourlyBuckets()));
  recoForYou = computed(() => this.discoverTracks().slice(0, 8));
  recoForYouPlayable = computed(() => this.recoForYou().map((t) => this.player.fromTrack(t)));
  discoverShown = computed(() => this.discoverTracks().slice(8));
  discoverShownPlayable = computed(() => this.discoverShown().map((t) => this.player.fromTrack(t)));
  madeForYou = computed(() => this.topTracks().slice(0, 8));
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
  sparkLine = computed(() => sparkLine(this.growthValues()));
  sparkArea = computed(() => sparkArea(this.growthValues(), this.sparkLine()));
  ngOnInit() {
    const discoverPage = (Math.floor(Date.now() / 86_400_000) % 120) + 5;
    this.dashboardSvc.getHomeFeed(discoverPage).subscribe({
      next: (feed) => {
        this.summary.set(feed.summary);
        if (feed.summary?.total_tracks) this.historySvc.pruneAbove(feed.summary.total_tracks);
        this.summaryLoading.set(false);
        this.topTracks.set(feed.top_tracks ?? []);
        const pts = feed.catalog_growth ?? [];
        this.growthLabels.set(pts.map((p) => p.label));
        this.growthValues.set(pts.map((p) => p.total || p.added));
        this.discoverTracks.set(feed.discover?.items ?? []);
        this.genres.set(feed.genres ?? []);
        this.artists.set(
          (feed.artists ?? []).map((a) => ({ id: a.id_artista, name: a.nombre_artista })),
        );
        this.playlists.set((feed.playlists ?? []).slice(0, 6));
        this.railsLoading.set(false);
      },
      error: (err) => {
        this.hasError.set(true);
        this.summaryLoading.set(false);
        this.railsLoading.set(false);
        console.error('[HomeComponent] getHomeFeed failed', err);
      },
    });
    this.historySvc.history$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((h) => {
        this.rawHistory.set(h);
        const deduped = dedupeHistory(h);
        this.history.set(deduped);
        deduped.forEach((entry) => this.resolveCover(entry.id_track));
      });
    this.historySvc.reload();
    this.favoritesSvc.favoriteIds$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((ids) => this.favoritesCount.set(ids.size));
  }
  cover(id: number | string): string {
    return this.covers.gradientFor(id);
  }
  /** Real cover URL for a track id (or null → gradient placeholder). */
  coverUrl(id: number): string | null {
    return this.coverUrls()[id] ?? null;
  }
  /** Resolve a real cover via the same service the player uses; cache per id. */
  private resolveCover(id: number): void {
    if (!id || id < 0 || this.coverUrls()[id] !== undefined) return;
    this.trackCover
      .cover$(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((url) => {
        if (url) this.coverUrls.update((m) => ({ ...m, [id]: url }));
      });
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
  fmt = fmtNumber;
  formatDurationMin = formatDurationMin;
  artistAffinity = artistAffinityPct;
  popularityKpi(): number | null {
    const v = this.summary()?.promedio_popularidad;
    return v != null ? Math.round(v * 10) / 10 : null;
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
}
