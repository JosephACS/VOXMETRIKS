import { SafeHtml } from '@angular/platform-browser';

import { IconRenderService } from '../../shared/services/icon-render.service';

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

import { TranslatePipe } from '../../shared/pipes/translate.pipe';

import { PlayableTrack } from '../../shared/models/player.models';



const ACCENTS = ['#7c3aed', '#1ed896', '#10b981', '#3b82f6', '#ec4899', '#f59e0b'];



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

  ],

  templateUrl: './recommendations.component.html',

  styleUrls: ['./recommendations.component.css'],

})

export class RecommendationsComponent implements OnInit {

  private iconRender = inject(IconRenderService);

  private stats = inject(StatsService);

  private userSvc = inject(UserService);

  covers = inject(CoverArtService);

  player = inject(MusicPlayerService);



  isLoading = signal(true);

  moodLoading = signal(false);

  hasError = signal(false);

  recsEnabled = signal(true);

  prefsLoaded = signal(false);

  data = signal<RecommendationPayload | null>(null);

  selectedMood = signal<string | null>(null);



  forYou = computed(() => this.data()?.for_you ?? []);

  artists = computed(() => this.data()?.artists ?? []);

  genres = computed(() => this.data()?.genres ?? []);

  moods = computed(() => this.data()?.moods ?? []);

  moodTracks = computed(() => this.data()?.mood_tracks ?? []);

  moodCount = computed(() => this.data()?.mood_count ?? 0);

  moodLabel = computed(() => this.data()?.mood_label ?? null);



  forYouPlayable = computed(() => this.forYou().map((t) => this.toPlayable(t)));

  moodTracksPlayable = computed(() => this.moodTracks().map((t) => this.toPlayable(t)));



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



  selectMood(id: string) {

    if (!this.recsEnabled()) return;

    const next = this.selectedMood() === id ? null : id;

    this.selectedMood.set(next);

    this.loadRecommendations(next ?? undefined, true);

  }



  private loadRecommendations(mood?: string, moodOnly = false) {

    if (!this.recsEnabled()) return;

    if (moodOnly) this.moodLoading.set(true);

    else this.isLoading.set(true);



    this.stats.getRecommendations(12, mood).subscribe({

      next: (d) => {

        this.data.set(d);

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



  toPlayable(t: RecTrack): PlayableTrack {

    const id = t.id_track ?? 0;

    return {

      id,

      title: t.nombre_track ?? '—',

      artist: primaryArtistName(t.nombre_artista),

      audioUrl: `/assets/audio/demo-${String((id % 8) + 1).padStart(2, '0')}.wav`,

      coverGradient: this.covers.gradientFor(id),

    };

  }



  accent(i: number): string {

    return ACCENTS[i % ACCENTS.length];

  }



  artistGradient(name?: string): string {

    return this.covers.gradientFor(name ?? 'artist');

  }



  artistInitial(name?: string): string {

    return primaryArtistName(name).charAt(0).toUpperCase();

  }



  displayArtist(name?: string): string {

    return primaryArtistName(name);

  }



  genreBarWidth(score: number): number {

    return Math.round(((score ?? 0) / this.maxGenreScore()) * 100);

  }



  icon(key: string, size = 18): SafeHtml {

    return this.iconRender.render(key, size);

  }

}
