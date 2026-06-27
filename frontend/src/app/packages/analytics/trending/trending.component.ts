import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { StatsService } from '../services/stats.service';
import { TopTrack } from '../../../shared/models/api.models';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

const COVER_GRADIENTS = [
  'linear-gradient(135deg, #1ed896, #148f5e)',
  'linear-gradient(135deg, #3b82f6, #1e40af)',
  'linear-gradient(135deg, #10b981, #047857)',
  'linear-gradient(135deg, #ec4899, #9d174d)',
  'linear-gradient(135deg, #f59e0b, #b45309)',
  'linear-gradient(135deg, #6366f1, #312e81)',
  'linear-gradient(135deg, #ef4444, #991b1b)',
  'linear-gradient(135deg, #14b8a6, #0f766e)',
];

@Component({
  selector: 'app-trending',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, DataSourceBadgeComponent, TranslatePipe],
  templateUrl: './trending.component.html',
  styleUrls: ['./trending.component.css'],
})
export class TrendingComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  player = inject(MusicPlayerService);

  isLoading = signal(true);
  hasError = signal(false);
  tracks = signal<TopTrack[]>([]);
  dailyStreams = signal<{ fecha: string; total_streams?: number }[]>([]);
  skeletonRows = Array(10).fill(0);

  streamChartValues = computed(() => {
    const daily = this.dailyStreams();
    if (!daily.length) return [0];
    const vals = daily.slice(-14).map((d) => d.total_streams ?? 0);
    const max = Math.max(...vals, 1);
    return vals.map((v) => Math.round((v / max) * 100));
  });

  topTrack = computed(() => this.tracks()[0] ?? null);

  chartDateLabels = computed(() => {
    const daily = this.dailyStreams().slice(-14);
    if (!daily.length) return [];
    const indexes = daily.length > 6
      ? [0, Math.floor((daily.length - 1) / 2), daily.length - 1]
      : daily.map((_, i) => i);
    const step = daily.length > 1 ? 390 / (daily.length - 1) : 0;
    return indexes.map((i) => ({
      x: i * step + 5,
      label: this.formatShortDate(daily[i]?.fecha),
    }));
  });

  maxDailyStreams = computed(() =>
    Math.max(...this.dailyStreams().slice(-14).map((d) => d.total_streams ?? 0), 0)
  );

  avgPopularity = computed(() => {
    const t = this.tracks();
    if (!t.length) return 0;
    return Math.round(t.reduce((s, x) => s + (x.popularity ?? 0), 0) / t.length);
  });

  maxPopularity = computed(() =>
    Math.max(...this.tracks().map((t) => t.popularity ?? 0), 0)
  );

  popDistribution = computed(() => {
    const t = this.tracks();
    const buckets = [
      { label: '90+', min: 90, color: '#1ed896', count: 0 },
      { label: '70', min: 70, color: '#7c3aed', count: 0 },
      { label: '50', min: 50, color: '#3b82f6', count: 0 },
      { label: '<50', min: 0, color: '#64748b', count: 0 },
    ];
    for (const track of t) {
      const p = track.popularity ?? 0;
      if (p >= 90) buckets[0].count++;
      else if (p >= 70) buckets[1].count++;
      else if (p >= 50) buckets[2].count++;
      else buckets[3].count++;
    }
    const max = Math.max(...buckets.map((b) => b.count), 1);
    return buckets.map((b) => ({ ...b, pct: Math.round((b.count / max) * 100) }));
  });

  constructor(private stats: StatsService) {}

  ngOnInit() {
    this.loadTrending();
  }

  loadTrending() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.stats.getTopTracks(25).subscribe({
      next: (d) => { this.tracks.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
    this.stats.getTrendingAnalytics(25).subscribe({
      next: (d) => { this.dailyStreams.set(d.daily_streams ?? []); },
      error: () => {},
    });
  }

  coverGradient(i: number): string {
    return COVER_GRADIENTS[i % COVER_GRADIENTS.length];
  }

  trackInitial(name?: string | null): string {
    return (name?.charAt(0) ?? '?').toUpperCase();
  }

  trendIconKey(i: number): string {
    const mod = i % 5;
    if (mod === 0 || mod === 1) return 'trend-up';
    if (mod === 2) return 'trend-down';
    return 'minus';
  }

  trendClass(i: number): string {
    const mod = i % 5;
    if (mod === 0 || mod === 1) return 'up';
    if (mod === 2) return 'down';
    return 'stable';
  }

  formatShortDate(value?: string): string {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value.slice(0, 5);
    return date.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' });
  }

  weeklyLine(): string {
    const data = this.streamChartValues();
    const step = data.length > 1 ? 390 / (data.length - 1) : 0;
    return data.map((v, i) => `${i * step + 5},${100 - v * 0.75}`).join(' ');
  }

  weeklyArea(): string {
    const data = this.streamChartValues();
    const step = data.length > 1 ? 390 / (data.length - 1) : 0;
    const pts = data.map((v, i) => `${i * step + 5},${100 - v * 0.75}`);
    const lastX = data.length > 1 ? (data.length - 1) * step + 5 : 5;
    return `5,100 ${pts.join(' ')} ${lastX},100`;
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  trackQueue() {
    return this.tracks().map((t) => this.player.fromTopTrack(t));
  }

  playHero() {
    const hero = this.topTrack();
    if (!hero) return;
    this.player.playTrack(this.player.fromTopTrack(hero), this.trackQueue());
  }
}
