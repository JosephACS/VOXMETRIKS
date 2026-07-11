import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GenresService } from '../../streaming/services/genres.service';
import { GeneroPopularidad } from '../../../shared/models/api.models';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

const GENRE_COLORS = ['#1ed896', '#148f5e', '#38bdf8', '#b794f6', '#f472b6', '#fbbf24', '#6366f1', '#ef4444'];

@Component({
  selector: 'app-comparatives',
  standalone: true,
  imports: [CommonModule, DataSourceBadgeComponent, TranslatePipe],
  templateUrl: './comparatives.component.html',
  styleUrls: ['./comparatives.component.css'],
})
export class ComparativesComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);

  isLoading = signal(true);
  hasError = signal(false);
  genres = signal<GeneroPopularidad[]>([]);
  skeletonRows = Array(8).fill(0);

  topGenres = computed(() => this.genres().slice(0, 6));

  heatmapGridColumns = computed(() => {
    const n = Math.max(this.topGenres().length, 1);
    return `80px repeat(${n}, minmax(52px, 1fr))`;
  });

  insights = computed(() => {
    const g = this.genres();
    const avgPop = g.length ? g.reduce((s, x) => s + (x.popularidad_promedio ?? 0), 0) / g.length : 0;
    const avgEn = g.length ? g.reduce((s, x) => s + (x.energia_promedio ?? 0), 0) / g.length : 0;
    const totalTracks = g.reduce((s, x) => s + (x.total_tracks ?? 0), 0);
    const top = g[0];
    return [
      { label: 'Géneros', value: g.length, iconKey: 'layers', trend: 'activos', trendClass: 'neutral' },
      { label: 'Popularidad media', value: avgPop.toFixed(1), iconKey: 'star', trend: `${avgPop.toFixed(1)} avg`, trendClass: 'neutral' },
      { label: 'Energía media', value: (avgEn * 100).toFixed(0) + '%', iconKey: 'zap', trend: 'estable', trendClass: 'neutral' },
      { label: 'Total canciones', value: this.fmt(totalTracks), iconKey: 'music', trend: top?.nombre_genero ?? '—', trendClass: 'neutral' },
    ];
  });

  constructor(private genresSvc: GenresService) {}

  ngOnInit() {
    this.loadComparatives();
  }

  loadComparatives() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.genresSvc.getGenreStats(1, 30).subscribe({
      next: (r) => { this.genres.set(r.items ?? []); this.isLoading.set(false); },
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
    const genres = this.topGenres();
    const n = Math.max(genres.length, 1);
    const cx = 140, cy = 140, r = 110;
    return genres.map((g, i) => {
      const fullLabel = g.nombre_genero ?? '?';
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const lx = cx + (r + 22) * Math.cos(angle);
      const ly = cy + (r + 22) * Math.sin(angle) + 3;
      const anchor = Math.abs(Math.cos(angle)) < 0.2 ? 'middle' : Math.cos(angle) > 0 ? 'start' : 'end';
      return {
        label: fullLabel.length > 10 ? fullLabel.slice(0, 9) + '…' : fullLabel,
        fullLabel,
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
        lx,
        ly,
        anchor,
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
    if (!top.length) return [];
    const trackMax = Math.max(...top.map((g) => g.total_tracks ?? 0), 1);
    const metrics: Array<{
      key: 'popularidad_promedio' | 'energia_promedio' | 'total_tracks';
      metric: string;
      toNorm: (raw: number) => number;
    }> = [
      { key: 'popularidad_promedio', metric: 'Popularidad', toNorm: (v) => v / 100 },
      { key: 'energia_promedio', metric: 'Energía', toNorm: (v) => v },
      { key: 'total_tracks', metric: 'Canciones', toNorm: (v) => v / trackMax },
    ];
    return metrics.map((m) => {
      const rawValues = top.map((g) => (g[m.key] as number | undefined) ?? 0);
      const norms = rawValues.map((v) => m.toNorm(v));
      const rowMax = Math.max(...norms, 0.001);
      return {
        metric: m.metric,
        cells: top.map((g, idx) => {
          const raw = rawValues[idx];
          const intensity = Math.min(Math.max(norms[idx] / rowMax, 0.05), 1);
          const displayVal = m.key === 'energia_promedio'
            ? `${Math.round(raw * 100)}%`
            : m.key === 'total_tracks'
              ? `${Math.round(raw)} canciones`
              : `${Math.round(raw)} pts`;
          return {
            genreId: g.id_genero,
            display: m.key === 'energia_promedio' ? `${Math.round(raw * 100)}` : `${Math.round(raw)}`,
            color: this.heatColor(intensity),
            tooltip: `${g.nombre_genero ?? 'Género'} · ${m.metric}: ${displayVal}`,
          };
        }),
      };
    });
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

  percent(value?: number | null, max = 1): number {
    const normalized = max === 100 ? (value ?? 0) : (value ?? 0) * 100;
    return Math.max(0, Math.min(100, normalized));
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
