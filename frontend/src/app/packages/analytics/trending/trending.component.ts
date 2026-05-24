import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { StatsService } from '../services/stats.service';
import { TopTrack } from '../../../shared/models/api.models';

const COVER_GRADIENTS = [
  'linear-gradient(135deg, #ff8c42, #7c3aed)',
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
  imports: [CommonModule, RouterModule, FavoriteBtnComponent],
  templateUrl: './trending.component.html',
  styleUrls: ['./trending.component.css'],
})
export class TrendingComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  isLoading = signal(true);
  hasError = signal(false);
  tracks = signal<TopTrack[]>([]);
  skeletonRows = Array(10).fill(0);

  weekLabels = [
    { x: 20, label: 'L' }, { x: 77, label: 'M' }, { x: 134, label: 'X' },
    { x: 191, label: 'J' }, { x: 248, label: 'V' }, { x: 305, label: 'S' }, { x: 362, label: 'D' },
  ];

  private weeklyData = [45, 62, 55, 78, 71, 88, 82, 95, 87, 92, 85, 98];

  topTrack = computed(() => this.tracks()[0] ?? null);

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
      { label: '90+', min: 90, color: '#ff8c42', count: 0 },
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
    this.stats.getTopTracks(25).subscribe({
      next: (d) => { this.tracks.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
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

  weeklyLine(): string {
    return this.weeklyData.map((v, i) => `${i * 33 + 5},${100 - v * 0.75}`).join(' ');
  }

  weeklyArea(): string {
    const pts = this.weeklyData.map((v, i) => `${i * 33 + 5},${100 - v * 0.75}`);
    return `5,100 ${pts.join(' ')} ${this.weeklyData.length * 33 - 28},100`;
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
