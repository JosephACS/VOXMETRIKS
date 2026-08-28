import { SafeHtml } from '@angular/platform-browser';

import { IconRenderService } from '../../shared/services/icon-render.service';

import { I18nService } from '../../core/services/i18n.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';

import { CommonModule } from '@angular/common';

import { RouterModule } from '@angular/router';

import { KpiCardComponent } from '../../shared/components/kpi-card/kpi-card.component';

import { MetricBarComponent } from '../../shared/components/metric-bar/metric-bar.component';

import { MediaCardComponent } from '../../shared/components/media-card/media-card.component';

import { FavoriteBtnComponent } from '../../shared/components/favorite-btn/favorite-btn.component';

import { StatsService } from '../analytics/services/stats.service';

import { UserService } from '../users/services/user.service';

import { RecommendationPayload } from '../../shared/models/api.models';

import { CoverArtService } from '../../shared/services/cover-art.service';

import { MusicPlayerService } from '../../shared/services/music-player.service';

import { primaryArtistName } from '../../shared/utils/artist.util';
import { displayTrackTitle } from '../../shared/utils/track-display.util';

import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../shared/components/data-source-badge/data-source-badge.component';

import { PlayableTrack } from '../../shared/models/player.models';
import {
  SpotifyIntegrationService,
  SpotifyTasteMixTrack,
} from '../../core/integrations/spotify/spotify-integration.service';



const ACCENTS = ['#e8a33d', '#d98a25', '#f0b555', '#c97816', '#e3a04a', '#b5650a'];



type RecTrack = NonNullable<RecommendationPayload['for_you']>[number];



@Component({

  selector: 'app-recommendations',

  standalone: true,

  imports: [

    CommonModule,

    RouterModule,

    KpiCardComponent,

    MetricBarComponent,

    MediaCardComponent,

    FavoriteBtnComponent,

    TranslatePipe,

    DataSourceBadgeComponent,

  ],

  templateUrl: './recommendations.component.html',

  styleUrls: ['./recommendations.component.css'],

})

export class RecommendationsComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private i18n = inject(I18nService);

  private iconRender = inject(IconRenderService);

  private stats = inject(StatsService);

  private userSvc = inject(UserService);

  covers = inject(CoverArtService);

  player = inject(MusicPlayerService);
  readonly spotify = inject(SpotifyIntegrationService);



  isLoading = signal(true);

  moodLoading = signal(false);

  hasError = signal(false);

  recsEnabled = signal(true);

  prefsLoaded = signal(false);

  data = signal<RecommendationPayload | null>(null);

  selectedMood = signal<string | null>(null);
  spotifyMix = signal<SpotifyTasteMixTrack[]>([]);
  spotifyCoverage = signal<{ spotify_signals: number; matched_catalog_tracks: number; match_percent: number } | null>(null);
  spotifyLoading = signal(false);
  spotifyError = signal(false);



  forYou = computed(() => this.data()?.for_you ?? []);

  artists = computed(() => this.data()?.artists ?? []);

  genres = computed(() => this.data()?.genres ?? []);

  moods = computed(() => this.data()?.moods ?? []);

  moodTracks = computed(() => this.data()?.mood_tracks ?? []);

  moodCount = computed(() => this.data()?.mood_count ?? 0);

  moodLabel = computed(() => this.data()?.mood_label ?? null);

  moodResultsLabel(): string {
    const count = this.moodCount();
    const key = count === 1 ? 'recommendations.mood.resultsCount' : 'recommendations.mood.resultsCountPlural';
    return this.i18n.t(key, { count });
  }



  forYouPlayable = computed(() => this.forYou().map((t) => this.toPlayable(t)));

  moodTracksPlayable = computed(() => this.moodTracks().map((t) => this.toPlayable(t)));
  spotifyMixPlayable = computed(() => this.spotifyMix().map((t) => this.toPlayable(t)));



  maxGenreScore = computed(() =>

    Math.max(...this.genres().map((g) => g.score ?? 0), 1)

  );



  kpiTracks = computed(() => this.forYou().length);

  kpiGenres = computed(() => this.genres().length);

  avgScore = computed(() => {

    const items = this.forYou();

    if (!items.length) return 0;

    return Math.round(

      items.reduce((s, t) => s + (t.recommendation_score ?? t.popularity ?? 0), 0) / items.length

    );

  });



  ngOnInit() {

    if (this.spotify.connected()) this.loadSpotifyMix();

    this.userSvc.getMe().subscribe({

      next: (p) => {

        this.recsEnabled.set(p.preferences?.recommendations_enabled ?? true);

        this.prefsLoaded.set(true);

        if (this.recsEnabled()) this.loadRecommendations();

        else this.isLoading.set(false);

      },

      error: () => {

        this.prefsLoaded.set(true);

        this.loadRecommendations();

      },

    });

  }

  loadSpotifyMix(): void {
    if (!this.spotify.connected() || this.spotifyLoading()) return;
    this.spotifyLoading.set(true);
    this.spotifyError.set(false);
    void this.spotify.buildTasteMix(16).then((mix) => {
      this.spotifyMix.set(mix.tracks ?? []);
      this.spotifyCoverage.set(mix.coverage);
      this.spotifyLoading.set(false);
    }).catch(() => {
      this.spotifyError.set(true);
      this.spotifyLoading.set(false);
    });
  }



  selectMood(id: string) {

    if (!this.recsEnabled()) return;

    const next = this.selectedMood() === id ? null : id;

    this.selectedMood.set(next);

    this.loadRecommendations(next ?? undefined, true);

  }

  retryRecommendations() {
    this.loadRecommendations(this.selectedMood() ?? undefined);
  }



  private loadRecommendations(mood?: string, moodOnly = false) {

    if (!this.recsEnabled()) return;

    if (moodOnly) this.moodLoading.set(true);

    else this.isLoading.set(true);

    this.hasError.set(false);



    this.stats.getRecommendations(12, mood).subscribe({

      next: (d) => {

        this.data.set(d);
        this.hasError.set(false);

        this.isLoading.set(false);

        this.moodLoading.set(false);

      },

      error: () => {

        this.hasError.set(true);

        this.isLoading.set(false);

        this.moodLoading.set(false);

      },

    });

  }



  toPlayable(t: RecTrack | SpotifyTasteMixTrack): PlayableTrack {

    const id = t.id_track ?? 0;

    return {

      id,

      title: displayTrackTitle(t.nombre_track),

      artist: primaryArtistName(t.nombre_artista),

      artistId: t.id_artista,

      audioUrl: '',

      coverGradient: this.covers.gradientFor(id),

      spotifyTrackId: 'spotify_track_id' in t ? t.spotify_track_id ?? undefined : undefined,

      spotifyUri: 'spotify_uri' in t ? t.spotify_uri ?? undefined : undefined,

    };

  }



  accent(i: number): string {

    return ACCENTS[i % ACCENTS.length];

  }



  artistGradient(name?: string): string {

    return this.covers.gradientFor(name ?? 'artist');

  }



  artistInitial(name?: string): string {

    return this.covers.initialsFor(primaryArtistName(name));

  }



  displayArtist(name?: string): string {

    return primaryArtistName(name);

  }



  displayTitle(name?: string): string {

    return displayTrackTitle(name);

  }



  genreBarWidth(score: number): number {

    return Math.round(((score ?? 0) / this.maxGenreScore()) * 100);

  }



  icon(key: string, size = 18): SafeHtml {

    return this.iconRender.render(key, size);

  }

}
