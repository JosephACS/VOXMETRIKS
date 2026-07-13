/**
 * MetricBarComponent
 * ==================
 * Barra de progreso inline reutilizable para celdas de tabla.
 * Muestra valor numérico + barra proporcional.
 *
 * Uso:
 *   <app-metric-bar [value]="72" [max]="100" color="primary" />
 *   <app-metric-bar [value]="0.85" [max]="1" color="info" suffix="" />
 */

import {
  Component,
  Input,
  ChangeDetectionStrategy,
} from '@angular/core';

@Component({
  selector: 'app-metric-bar',
  standalone: true,
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="metric-bar-wrap">
      <div class="metric-bar">
        <div
          class="metric-bar-fill"
          [style.width]="fillWidth"
          [style.background]="fillColor"
        ></div>
      </div>
      <span class="metric-value font-mono">
        {{ displayValue }}{{ suffix }}
      </span>
    </div>
  `,
  styles: [`
    .metric-bar-wrap {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      width: 100%;
    }

    .metric-bar {
      flex: 1;
      height: 4px;
      background: var(--color-surface-3);
      border-radius: 2px;
      overflow: hidden;
      min-width: 40px;
    }

    .metric-bar-fill {
      height: 100%;
      border-radius: 2px;
      background: var(--color-primary);
      transition: width 0.3s ease;
    }

    .metric-value {
      font-size: 0.72rem;
      color: var(--color-text-secondary);
      min-width: 36px;
      text-align: right;
      flex-shrink: 0;
    }
  `],
})
export class MetricBarComponent {
  /** Valor numérico a mostrar */
  @Input({ required: true }) value: number | null = null;
  /** Valor máximo para el cálculo de la barra */
  @Input() max = 100;
  /** Color semántico o CSS custom property */
  @Input() color: 'primary' | 'info' | 'warning' | 'danger' | 'success' = 'primary';
  /** Decimales a mostrar: '1.0-0', '1.2-2', etc. */
  @Input() digitsInfo = '1.0-1';
  /** Sufijo visual tras el número */
  @Input() suffix = '';
  /** Porcentaje mínimo de relleno (evita bars invisibles) */
  @Input() minFill = 2;

  private readonly colorMap: Record<string, string> = {
    primary: 'var(--color-primary)',
    info:    'var(--color-info)',
    warning: 'var(--color-warning)',
    danger:  'var(--color-danger)',
    success: 'var(--color-success)',
  };

  get fillColor(): string {
    return this.colorMap[this.color] ?? this.colorMap['primary'];
  }

  get fillWidth(): string {
    const v = this.value ?? 0;
    const m = this.max || 1;
    const pct = Math.min(100, Math.max(this.minFill, (v / m) * 100));
    return `${Math.round(pct)}%`;
  }

  get displayValue(): string {
    const v = this.value ?? 0;
    // Simple formatting without DecimalPipe (used as template pipe)
    const [, fracSpec] = this.digitsInfo.split('.');
    if (!fracSpec) return String(Math.round(v));
    const [, maxFrac] = fracSpec.split('-').map(Number);
    return v.toFixed(maxFrac ?? 1);
  }
}
