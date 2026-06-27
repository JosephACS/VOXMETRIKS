import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../services/stats.service';
import { GenresService } from '../../streaming/services/genres.service';
import { DistribucionEnergia, GeneroPopularidad } from '../../../shared/models/api.models';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule, DataSourceBadgeComponent, TranslatePipe],
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.css'],
})
export class AnalyticsComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  isLoading    = signal(true);
  partialError = signal(false);
  energyDist   = signal<DistribucionEnergia[]>([]);
  genreStats   = signal<GeneroPopularidad[]>([]);
  engagement   = signal<{ skip_rate?: number; completion_rate?: number; engagement_score?: number; avg_session_time_min?: number } | null>(null);
  maxTracks    = computed(() => Math.max(...this.genreStats().map(g => g.total_tracks ?? 0), 1));
  maxEnergy    = computed(() => Math.max(...this.energyDist().map(e => e.cantidad_tracks ?? 0), 1));
  topGenres    = computed(() => this.genreStats().slice(0, 12));
  totalTracks  = computed(() => this.genreStats().reduce((s, g) => s + (g.total_tracks ?? 0), 0));
  avgPop       = computed(() => {
    const g = this.genreStats().filter(x => x.popularidad_promedio);
    return g.length ? +(g.reduce((s, x) => s + (x.popularidad_promedio ?? 0), 0) / g.length).toFixed(1) : 0;
  });
  avgEnergy    = computed(() => {
    const g = this.genreStats().filter(x => x.energia_promedio);
    return g.length ? +(g.reduce((s, x) => s + (x.energia_promedio ?? 0), 0) / g.length * 100).toFixed(1) : 0;
  });

  constructor(private stats: StatsService, private genres: GenresService) {}

  ngOnInit() {
    this.loadAnalytics();
  }

  loadAnalytics() {
    this.isLoading.set(true);
    this.partialError.set(false);
    let completed = 0;
    let failed = 0;
    const done = (ok: boolean) => {
      completed += 1;
      if (!ok) failed += 1;
      if (completed >= 3) {
        this.partialError.set(failed > 0);
        this.isLoading.set(false);
      }
    };

    this.stats.getEnergyDistribution().subscribe({ next: d => { this.energyDist.set(d ?? []); done(true); }, error: () => done(false) });
    this.genres.getGenreStats(1, 50).subscribe({ next: r => { this.genreStats.set(r.items ?? []); done(true); }, error: () => done(false) });
    this.stats.getEngagementAnalytics().subscribe({
      next: d => { this.engagement.set(d); done(true); },
      error: () => done(false),
    });
  }

  energyBarH(count: number): number { return Math.round((count / this.maxEnergy()) * 100); }
  trackBarW(tracks: number): number { return Math.round((tracks / this.maxTracks()) * 100); }
  genreColor(i: number): string { return `hsl(${(i * 37) % 360},65%,55%)`; }
  popWidth(value?: number | null): number { return Math.max(0, Math.min(100, value ?? 0)); }
  energyWidth(value?: number | null): number { return Math.max(0, Math.min(100, (value ?? 0) * 100)); }
  skeletonRows = Array(8).fill(0);

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
