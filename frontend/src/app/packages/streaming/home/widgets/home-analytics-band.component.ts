import { Component, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { I18nService } from '../../../../core/services/i18n.service';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { KpiCardComponent } from '../../../../shared/components/kpi-card/kpi-card.component';
import { GeneroPopularidad, StatsSummary } from '../../../../shared/models/api.models';
import { artistAffinityPct, barHeightPct, fmtNumber } from '../home-format.util';
import { KPI_TRENDS } from '../home-metrics.util';

export interface HomeActivityItem {
  id_track: number;
  viewed_at: string;
  rel: string;
  label: string;
}

@Component({
  selector: 'app-home-analytics-band',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, KpiCardComponent],
  templateUrl: './home-analytics-band.component.html',
  styleUrls: ['../home.component.css'],
})
export class HomeAnalyticsBandComponent {
  readonly lang = inject(I18nService).lang;

  readonly summary = input<StatsSummary | null>(null);
  readonly summaryLoading = input(false);
  readonly playlistCount = input(0);
  readonly favoritesCount = input(0);
  readonly listenMinutesToday = input(0);
  readonly growthValues = input<number[]>([]);
  readonly sparkLine = input('');
  readonly sparkArea = input('');
  readonly hourlyBuckets = input<number[]>([]);
  readonly peakHour = input(0);
  readonly hasHistoryData = input(false);
  readonly genreBars = input<{ name: string; pct: number; tracks: number }[]>([]);
  readonly artists = input<{ id: number; name: string }[]>([]);
  readonly genres = input<GeneroPopularidad[]>([]);
  readonly weeklyTimePct = input(0);
  readonly weeklyTimeLabel = input('');
  readonly activityFeed = input<HomeActivityItem[]>([]);
  readonly weeklyGoalPct = input(0);
  readonly weeklyDiscoverCount = input(0);
  readonly topGenre = input<string | null>(null);
  readonly topArtist = input<string | null>(null);
  readonly kpiSkels = input<number[]>([1, 2, 3, 4, 5, 6, 7, 8]);

  fmt = fmtNumber;
  barHeight = barHeightPct;
  artistAffinity = artistAffinityPct;

  kpiTrend(key: string) {
    return KPI_TRENDS[key] ?? null;
  }
}
