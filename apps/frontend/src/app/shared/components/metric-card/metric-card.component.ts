import { Component, input } from '@angular/core';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-metric-card',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './metric-card.component.html',
  styleUrl: './metric-card.component.scss',
})
export class MetricCardComponent {
  readonly title = input.required<string>();
  readonly value = input<number | string | null>(null);
  readonly icon = input('');
  readonly trendPct = input<number | null>(null);
  readonly subtitle = input<string | null>(null);
  readonly loading = input(false);

  trendPositive(): boolean | null {
    const t = this.trendPct();
    if (t == null) return null;
    return t >= 0;
  }
}
