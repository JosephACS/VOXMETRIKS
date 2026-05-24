import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GenresService } from '../../streaming/services/genres.service';
import { GeneroPopularidad } from '../../../shared/models/api.models';

const GENRE_COLORS = ['#1ed896', '#148f5e', '#38bdf8', '#b794f6', '#f472b6', '#fbbf24', '#6366f1', '#ef4444'];

@Component({
  selector: 'app-comparatives',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './comparatives.component.html',
  styleUrls: ['./comparatives.component.css'],
})
export class ComparativesComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  isLoading = signal(true);
  hasError = signal(false);
  genres = signal<GeneroPopularidad[]>([]);
  skeletonRows = Array(8).fill(0);

  topGenres = computed(() => this.genres().slice(0, 6));

  insights = computed(() => {
    const g = this.genres();
    const avgPop = g.length ? g.reduce((s, x) => s + (x.popularidad_promedio ?? 0), 0) / g.length : 0;
    const avgEn = g.length ? g.reduce((s, x) => s + (x.energia_promedio ?? 0), 0) / g.length : 0;
    const totalTracks = g.reduce((s, x) => s + (x.total_tracks ?? 0), 0);
    const top = g[0];
    return [
      { label: 'Géneros', value: g.length, iconKey: 'layers', trend: 'activos', trendClass: 'neutral' },
      { label: 'Popularidad media', value: avgPop.toFixed(1), iconKey: 'star', trend: '+2.4%', trendClass: 'up' },
      { label: 'Energía media', value: (avgEn * 100).toFixed(0) + '%', iconKey: 'zap', trend: 'estable', trendClass: 'neutral' },
      { label: 'Total canciones', value: this.fmt(totalTracks), iconKey: 'music', trend: top?.nombre_genero ?? '—', trendClass: 'neutral' },
    ];
  });

  constructor(private genresSvc: GenresService) {}

  ngOnInit() {
    this.genresSvc.getGenreStats(30).subscribe({
      next: (d) => { this.genres.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  radarRings(): { r: number; points: string }[] {
    return [0.25, 0.5, 0.75, 1].map((scale) => ({
      r: 100 * scale,
      points: this.radarRingPoints(scale),
    }));
  }

  radarAxes = computed(() => {
    const labels = this.topGenres().map((g) => this.genreShort(g.nombre_genero));
    const n = Math.max(labels.length, 1);
    const cx = 140, cy = 140, r = 110;
    return labels.map((label, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      return {
        label,
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
        lx: cx + (r + 18) * Math.cos(angle),
        ly: cy + (r + 18) * Math.sin(angle) + 3,
      };
    });
  });

  radarPopPoints(): string {
    return this.radarDataPoints((g) => (g.popularidad_promedio ?? 0) / 100);
  }

  radarEnergyPoints(): string {
    return this.radarDataPoints((g) => g.energia_promedio ?? 0);
  }

  heatmapRows = computed(() => {
    const top = this.topGenres();
    const metrics = [
      { key: 'popularidad_promedio' as const, metric: 'Popularidad', max: 100, scale: 1 },
      { key: 'energia_promedio' as const, metric: 'Energía', max: 1, scale: 1 },
      { key: 'total_tracks' as const, metric: 'Canciones', max: Math.max(...top.map((g) => g.total_tracks ?? 0), 1), scale: 1 },
    ];
    return metrics.map((m) => ({
      metric: m.metric,
      cells: top.map((g) => {
        const raw = (g[m.key] as number | undefined) ?? 0;
        const norm = m.key === 'energia_promedio' ? raw : raw / m.max;
        const intensity = Math.min(Math.max(norm, 0), 1);
        return {
          genreId: g.id_genero,
          display: m.key === 'energia_promedio' ? `${Math.round(raw * 100)}` : `${Math.round(raw)}`,
          color: this.heatColor(intensity),
          tooltip: `${g.nombre_genero}: ${raw}`,
        };
      }),
    }));
  });

  genreColor(i: number): string {
    return GENRE_COLORS[i % GENRE_COLORS.length];
  }

  genreShort(name?: string | null): string {
    if (!name) return '?';
    return name.length > 6 ? name.slice(0, 5) + '…' : name;
  }

  compositeScore(g: GeneroPopularidad): string {
    const score = ((g.popularidad_promedio ?? 0) * 0.6 + (g.energia_promedio ?? 0) * 100 * 0.4);
    return score.toFixed(0);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  fmt(val: number): string {
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toString();
  }

  private radarRingPoints(scale: number): string {
    const n = Math.max(this.topGenres().length, 3);
    const cx = 140, cy = 140, r = 100 * scale;
    return Array.from({ length: n }, (_, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
    }).join(' ');
  }

  private radarDataPoints(fn: (g: GeneroPopularidad) => number): string {
    const top = this.topGenres();
    const n = Math.max(top.length, 1);
    const cx = 140, cy = 140, r = 100;
    return top.map((g, i) => {
      const val = Math.min(Math.max(fn(g), 0), 1);
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      return `${cx + r * val * Math.cos(angle)},${cy + r * val * Math.sin(angle)}`;
    }).join(' ');
  }

  private heatColor(intensity: number): string {
    const r = Math.round(255 * intensity * 0.55 + 30);
    const g = Math.round(140 * intensity * 0.4 + 20);
    const b = Math.round(66 + intensity * 80);
    const a = 0.15 + intensity * 0.55;
    return `rgba(${r}, ${g}, ${b}, ${a})`;
  }
}
