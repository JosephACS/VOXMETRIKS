import { SafeHtml } from '@angular/platform-browser';

import { IconRenderService } from '../../shared/services/icon-render.service';

import { Component, inject, OnInit, signal, computed } from '@angular/core';

import { CommonModule } from '@angular/common';

import { RouterModule } from '@angular/router';

import { KpiCardComponent } from '../../shared/components/kpi-card/kpi-card.component';

import { MetricBarComponent } from '../../shared/components/metric-bar/metric-bar.component';

import { StatsService } from '../analytics/services/stats.service';

import { RecommendationPayload } from '../../shared/models/api.models';

import { CoverArtService } from '../../shared/services/cover-art.service';

import { primaryArtistName } from '../../shared/utils/artist.util';



const ACCENTS = ['#7c3aed', '#1ed896', '#10b981', '#3b82f6', '#ec4899', '#f59e0b'];



@Component({

  selector: 'app-recommendations',

  standalone: true,

  imports: [CommonModule, RouterModule, KpiCardComponent, MetricBarComponent],

  templateUrl: './recommendations.component.html',

  styleUrls: ['./recommendations.component.css'],

})

export class RecommendationsComponent implements OnInit {

  private iconRender = inject(IconRenderService);

  private stats = inject(StatsService);

  private covers = inject(CoverArtService);



  isLoading = signal(true);

  moodLoading = signal(false);

  hasError = signal(false);

  data = signal<RecommendationPayload | null>(null);

  selectedMood = signal<string | null>(null);



  forYou = computed(() => this.data()?.for_you ?? []);

  artists = computed(() => this.data()?.artists ?? []);

  genres = computed(() => this.data()?.genres ?? []);

  moods = computed(() => this.data()?.moods ?? []);

  moodTracks = computed(() => this.data()?.mood_tracks ?? []);

  moodCount = computed(() => this.data()?.mood_count ?? 0);

  moodLabel = computed(() => this.data()?.mood_label ?? null);



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

    this.loadRecommendations();

  }



  selectMood(id: string) {

    const next = this.selectedMood() === id ? null : id;

    this.selectedMood.set(next);

    this.loadRecommendations(next ?? undefined, true);

  }



  private loadRecommendations(mood?: string, moodOnly = false) {

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

