import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../services/stats.service';
import { GenresService } from '../../streaming/services/genres.service';
import { DistribucionEnergia, GeneroPopularidad } from '../../../shared/models/api.models';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.css'],
})
export class AnalyticsComponent implements OnInit {
  isLoading    = signal(true);
  energyDist   = signal<DistribucionEnergia[]>([]);
  genreStats   = signal<GeneroPopularidad[]>([]);
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
    let n = 0; const done = () => { if (++n >= 2) this.isLoading.set(false); };
    this.stats.getEnergyDistribution().subscribe({ next: d => { this.energyDist.set(d ?? []); done(); }, error: () => done() });
    this.genres.getGenreStats(50).subscribe({ next: d => { this.genreStats.set(d ?? []); done(); }, error: () => done() });
  }

  energyBarH(count: number): number { return Math.round((count / this.maxEnergy()) * 100); }
  trackBarW(tracks: number): number { return Math.round((tracks / this.maxTracks()) * 100); }
  genreColor(i: number): string { return `hsl(${(i * 37) % 360},65%,55%)`; }
  skeletonRows = Array(8).fill(0);
}
