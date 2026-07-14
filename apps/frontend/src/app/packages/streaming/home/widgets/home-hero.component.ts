import { Component, computed, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { I18nService } from '../../../../core/services/i18n.service';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { EventsBreakdown, StatsSummary } from '../../../../shared/models/api.models';
import { StatsService } from '../../../analytics/services/stats.service';
import { fmtNumber } from '../home-format.util';

export type EventsCopyMode = 'synthetic' | 'mixed' | 'unknown';

@Component({
  selector: 'app-home-hero',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  templateUrl: './home-hero.component.html',
  styleUrls: ['../home.component.css'],
})
export class HomeHeroComponent {
  private readonly stats = inject(StatsService);
  readonly lang = inject(I18nService).lang;

  readonly greetingKey = input.required<string>();
  readonly userName = input.required<string>();
  readonly userPlan = input.required<string>();
  readonly summary = input<StatsSummary | null>(null);
  readonly summaryLoading = input(false);
  readonly playlistCount = input(0);
  readonly listenStreak = input(0);
  readonly listenMinutesToday = input(0);
  readonly weeklyGoalPct = input(0);
  readonly explorerLevel = input(1);
  readonly heroStatSkels = input<number[]>([1, 2, 3, 4, 5]);

  readonly eventsOpen = signal(false);
  readonly eventsLoading = signal(false);
  readonly eventsError = signal('');
  readonly eventsBreakdown = signal<EventsBreakdown | null>(null);

  /** Prefer breakdown when loaded; otherwise summary classification totals. */
  readonly eventsCopyMode = computed<EventsCopyMode>(() => {
    const totals =
      this.eventsBreakdown()?.classification_totals
      ?? this.summary()?.events_classification_totals
      ?? null;
    return classifyEventsCopyMode(totals);
  });

  readonly eventsSubKey = computed(() => {
    const mode = this.eventsCopyMode();
    if (mode === 'synthetic') return 'home.stat.eventsSubSynthetic';
    if (mode === 'unknown') return 'home.stat.eventsSubUnknown';
    return 'home.stat.eventsSubMixed';
  });

  readonly eventsTipKey = computed(() =>
    this.eventsCopyMode() === 'unknown' ? 'home.stat.eventsTipUnknown' : 'home.stat.eventsTip',
  );

  fmt = fmtNumber;

  exact(n: number | null | undefined): string {
    if (n == null) return '—';
    return n.toLocaleString(this.lang() === 'en' ? 'en-US' : 'es-ES');
  }

  openEventsBreakdown(): void {
    this.eventsOpen.set(true);
    this.eventsError.set('');
    if (this.eventsBreakdown()) return;
    this.eventsLoading.set(true);
    this.stats.getEventsBreakdown().subscribe({
      next: (d) => {
        this.eventsBreakdown.set(d);
        this.eventsLoading.set(false);
      },
      error: () => {
        this.eventsLoading.set(false);
        this.eventsError.set(this.lang() === 'en'
          ? 'Could not load the analytical events breakdown.'
          : 'No se pudo cargar el desglose de eventos analíticos.');
      },
    });
  }

  closeEventsBreakdown(): void {
    this.eventsOpen.set(false);
  }

  explorerQuery(table: string): Record<string, string> {
    return { table };
  }
}

/** Does not invent classifications — only mirrors reported totals. */
export function classifyEventsCopyMode(
  totals: Record<string, number> | null | undefined,
): EventsCopyMode {
  if (!totals) return 'unknown';
  const synthetic = Number(totals['synthetic'] ?? 0);
  const unknown = Number(totals['unknown'] ?? 0);
  const real = Number(totals['real'] ?? 0);
  const imported = Number(totals['imported'] ?? 0);
  const demo = Number(totals['demo'] ?? 0);
  const knownOther = real + imported + demo;
  const total = synthetic + unknown + knownOther;
  if (total <= 0) return 'unknown';
  if (unknown > 0 && knownOther === 0 && synthetic === 0) return 'unknown';
  if (synthetic === total) return 'synthetic';
  if (unknown === total) return 'unknown';
  if (unknown > 0) return 'unknown';
  if (synthetic > 0 && knownOther > 0) return 'mixed';
  if (knownOther === total) return 'mixed';
  return 'mixed';
}
