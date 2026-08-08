import { Component, computed, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { I18nService } from '../../../../core/services/i18n.service';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { EventsBreakdown, StatsSummary } from '../../../../shared/models/api.models';
import { StatsService } from '../../../analytics/services/stats.service';
import { fmtNumber } from '../home-format.util';
import { classifyEventsCopyMode, EventsCopyMode } from '../home-metrics.util';

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
  readonly listenStreak = input(0);
  readonly listenMinutesToday = input(0);
  readonly weeklyGoalPct = input(0);
  readonly explorerLevel = input(1);
  /** Kept for events classification fallback while the breakdown modal loads. */
  readonly summary = input<StatsSummary | null>(null);

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
