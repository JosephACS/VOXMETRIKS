import { Component, computed, inject, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { I18nService } from '../../../../core/services/i18n.service';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { KpiCardComponent } from '../../../../shared/components/kpi-card/kpi-card.component';
import { GeneroPopularidad, StatsSummary } from '../../../../shared/models/api.models';
import { artistAffinityPct, barHeightPct, fmtNumber } from '../home-format.util';
import { classifyEventsCopyMode, EventsCopyMode } from '../home-metrics.util';

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
  readonly favoritesCount = input(0);
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

  /** Opens the warehouse events breakdown dialog hosted by the hero shell. */
  readonly openCatalogEvents = output<void>();

  fmt = fmtNumber;
  barHeight = barHeightPct;
  artistAffinity = artistAffinityPct;

  readonly eventsCopyMode = computed<EventsCopyMode>(() =>
    classifyEventsCopyMode(this.summary()?.events_classification_totals ?? null),
  );

  readonly eventsSubKey = computed(() => {
    const mode = this.eventsCopyMode();
    if (mode === 'synthetic') return 'home.stat.eventsSubSynthetic';
    if (mode === 'unknown') return 'home.stat.eventsSubUnknown';
    return 'home.stat.eventsSubMixed';
  });

  readonly eventsTipKey = computed(() =>
    this.eventsCopyMode() === 'unknown' ? 'home.stat.eventsTipUnknown' : 'home.stat.eventsTip',
  );

  exact(n: number | null | undefined): string {
    if (n == null) return '—';
    return n.toLocaleString(this.lang() === 'en' ? 'en-US' : 'es-ES');
  }
}
