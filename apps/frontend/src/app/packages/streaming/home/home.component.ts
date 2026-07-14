import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DashboardService } from '../services/dashboard.service';
import { AuthService } from '../../../core/services/auth.service';
import { HistoryService } from '../services/history.service';
import { ListenStatsService } from '../services/listen-stats.service';
import { FavoritesService } from '../services/favorites.service';
import { PlayerController } from '../../../playback-core/player.controller';
import { toPlayableFromHistory } from '../../../playback-core/adapters/track.adapter';
import { TrackActionsComponent } from '../../../shared/components/track-actions/track-actions.component';
import {
  StatsSummary, GeneroPopularidad, HistoryEntry, PlaylistSummary, Track,
} from '../../../shared/models/api.models';
import { PlayableTrack } from '../../../shared/models/player.models';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import {
  catalogGrowthTrend,
  dedupeHistory,
  genreBars,
  historyArtists,
  hourlyBuckets,
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
import { SmartHomeService } from '../../smart/services/smart-home.service';
import { HomeSectionWidgetComponent } from '../../smart/widgets/home-section-widget.component';
import { SmartHomeSection, AudioDna } from '../../smart/models/smart-home.models';
import { AudioPrefetchService } from '../../../playback-core/audio-prefetch.service';
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule, RouterModule, HorizontalSectionComponent, MediaCardComponent,
    TranslatePipe, HomeHeroComponent, HomeAnalyticsBandComponent, TrackActionsComponent,
    HomeSectionWidgetComponent,
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  private dashboardSvc = inject(DashboardService);
  private smartHomeSvc = inject(SmartHomeService);
  private historySvc = inject(HistoryService);
  private listenStats = inject(ListenStatsService);
  private auth = inject(AuthService);
  private favoritesSvc = inject(FavoritesService);
  readonly controller = inject(PlayerController);
  private destroyRef = inject(DestroyRef);
  private covers = inject(CoverArtService);
  private trackCover = inject(TrackCoverService);
  private audioPrefetch = inject(AudioPrefetchService);
  private i18n = inject(I18nService);
  /** Resolved real cover URLs per track id (same source the player uses). */
  private coverUrls = signal<Record<number, string>>({});
  /** Artist portrait URLs keyed by artist id. */
  private artistCoverUrls = signal<Record<number, string>>({});
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
  discoverTracks = signal<Track[]>([]);
  genres = signal<GeneroPopularidad[]>([]);
  artists = signal<{ id: number; name: string }[]>([]);
  playlists = signal<PlaylistSummary[]>([]);
  myPlaylistCount = signal(0);
  history = signal<HistoryEntry[]>([]);
  rawHistory = signal<HistoryEntry[]>([]);
  favoritesCount = signal(0);
  smartSections = signal<SmartHomeSection[]>([]);
  audioDna = signal<AudioDna | null>(null);
  smartLoading = signal(true);
  growthLabels = signal<string[]>([]);
  growthValues = signal<number[]>([]);
  readonly heroStatSkels = [1, 2, 3, 4, 5];
  readonly kpiSkels = [1, 2, 3, 4, 5, 6, 7, 8];
  userName = computed(() => this.auth.getUser()?.username ?? 'demo');
  userPlan = computed(() => this.auth.getUser()?.plan ?? 'Free');
  listenStreak = computed(() => listenStreak(this.rawHistory()));
  listenMinutesToday = computed(() => this.listenStats.minutesToday());
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
  recoForYou = computed(() => {
    const smart = this.smartSections().find((s) => s.id === 'recommended-for-you');
    if (smart?.tracks?.length) {
      return smart.tracks.map((t) => ({
        id_track: t.id_track,
        nombre_track: t.nombre_track ?? '',
        nombre_artista: t.nombre_artista,
        popularity: t.popularity,
      } as Track));
    }
    return this.discoverTracks().slice(0, 8);
  });
  recoForYouPlayable = computed(() => this.recoForYou().map((t) => this.controller.fromTrack(t)));
  discoverShown = computed(() => this.discoverTracks().slice(8));
  discoverShownPlayable = computed(() => this.discoverShown().map((t) => this.controller.fromTrack(t)));
  historyPlayableQueue = computed(() => this.history().map((h) => this.historyPlayable(h)));
  topGenre = computed(() => this.genres()[0]?.nombre_genero?.trim() || null);
  topArtist = computed(() => this.artists()[0]?.name?.trim() || null);
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
    && !this.recoForYou().length
    && !this.discoverTracks().length
    && !this.artists().length
    && !this.playlists().length
    && !this.genres().length
  );
  sparkLine = computed(() => sparkLine(this.growthValues()));
  sparkArea = computed(() => sparkArea(this.growthValues(), this.sparkLine()));
  ngOnInit() {
    this.listenStats.reload();
    const discoverPage = (Math.floor(Date.now() / 86_400_000) % 120) + 5;
    this.dashboardSvc.getHomeFeed(discoverPage).subscribe({
      next: (feed) => {
        this.summary.set(feed.summary);
        if (feed.summary?.total_tracks) this.historySvc.pruneAbove(feed.summary.total_tracks);
        this.summaryLoading.set(false);
        const pts = feed.catalog_growth ?? [];
        this.growthLabels.set(pts.map((p) => p.label));
        this.growthValues.set(pts.map((p) => p.total || p.added));
        this.discoverTracks.set(feed.discover?.items ?? []);
        this.genres.set(feed.genres ?? []);
        this.artists.set(
          (feed.artists ?? []).map((a) => ({ id: a.id_artista, name: a.nombre_artista })),
        );
        this.playlists.set((feed.playlists ?? []).slice(0, 6));
        this.myPlaylistCount.set(feed.my_playlist_count ?? 0);
        this.railsLoading.set(false);
        (feed.discover?.items ?? []).forEach((t) => this.resolveCover(t.id_track, t.id_artista));
        (feed.artists ?? []).forEach((a) => this.resolveArtistCover(a.id_artista));
        this.audioPrefetch.warm(
          (feed.discover?.items ?? []).map((t) => t.id_track),
          10,
        );
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
        this.audioPrefetch.warm(deduped.map((e) => e.id_track), 8);
      });
    this.historySvc.reload();
    this.favoritesSvc.favoriteIds$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((ids) => this.favoritesCount.set(ids.size));

    this.smartHomeSvc.getHome().subscribe({
      next: (res) => {
        this.smartSections.set(res.sections ?? []);
        this.audioDna.set(res.profile?.audio_dna ?? null);
        this.smartLoading.set(false);
        const smartIds: number[] = [];
        res.sections?.forEach((s) =>
          s.tracks?.forEach((t) => {
            this.resolveCover(t.id_track);
            smartIds.push(t.id_track);
          }),
        );
        this.audioPrefetch.warm(smartIds, 12);
      },
      error: (err) => {
        this.smartLoading.set(false);
        console.error('[HomeComponent] smart home failed', err);
      },
    });
  }
  cover(id: number | string): string {
    return this.covers.gradientFor(id);
  }
  /** Real cover URL for a track id (or null → gradient placeholder). */
  coverUrl(id: number): string | null {
    return this.coverUrls()[id] ?? null;
  }
  artistCoverUrl(id: number): string | null {
    return this.artistCoverUrls()[id] ?? null;
  }
  /** Resolve track cover (album art, then artist portrait). */
  private resolveCover(id: number, artistId?: number | null): void {
    if (!id || id < 0 || this.coverUrls()[id] !== undefined) return;
    this.trackCover
      .bestCover$(id, artistId ?? undefined)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((url) => {
        if (url) this.coverUrls.update((m) => ({ ...m, [id]: url }));
      });
  }
  private resolveArtistCover(artistId: number): void {
    if (!artistId || artistId < 0 || this.artistCoverUrls()[artistId] !== undefined) return;
    this.trackCover
      .artistCover$(artistId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((url) => {
        if (url) this.artistCoverUrls.update((m) => ({ ...m, [artistId]: url }));
      });
  }
  historyPlayable(h: HistoryEntry): PlayableTrack {
    return toPlayableFromHistory(this.covers, h);
  }

  playHistory(h: HistoryEntry, e?: Event) {
    e?.stopPropagation();
    this.controller.playTrack(this.historyPlayable(h), this.historyPlayableQueue());
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
  artistOfDay = computed(() => this.artists()[0]?.name ?? null);
}
