/**
 * KpiCardComponent
 * ================
 * Tarjeta de métrica reutilizable para el dashboard.
 *
 * API unificada — acepta tanto el contrato del spec (value: number|null, subtitle)
 * como el contrato extendido (trend, color) sin breaking changes.
 */

import { Component, Input } from '@angular/core';
import { DecimalPipe }      from '@angular/common';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [DecimalPipe],
  template: `
    <div class="kpi-card" [class]="'kpi-card kpi-color-' + color">
      <div class="kpi-header">
        <span class="kpi-icon">{{ icon }}</span>
        <span class="kpi-label">{{ label }}</span>
      </div>

      <div class="kpi-value">
        @if (value !== null && value !== undefined) {
          {{ value | number }}
        } @else {
          <span class="kpi-skeleton"></span>
        }
      </div>

      @if (subtitle) {
        <div class="kpi-subtitle">{{ subtitle }}</div>
      }

      @if (trend) {
        <div class="kpi-trend" [class]="trendClass">
          {{ trend }}
          @if (trendLabel) { <span class="trend-label">{{ trendLabel }}</span> }
        </div>
      }
    </div>
  `,
  styles: [`
    .kpi-card {
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 0.625rem;
      padding: 1.25rem;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      overflow: hidden;
      transition: transform var(--transition), border-color var(--transition), box-shadow var(--transition);
      cursor: default;
    }

    .kpi-card::before {
      content: '';
      position: absolute;
      inset: 0 0 auto 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
      opacity: 0;
      transition: opacity var(--transition);
    }

    .kpi-card:hover {
      transform: translateY(-3px);
      border-color: var(--color-border-hover);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    .kpi-card:hover::before { opacity: 1; }

    /* ── Color variants ── */
    .kpi-color-primary { border-color: rgba(34, 197, 94, 0.2); }
    .kpi-color-primary:hover { border-color: rgba(34, 197, 94, 0.4); box-shadow: 0 8px 32px rgba(34, 197, 94, 0.1); }
    .kpi-color-primary .kpi-value { color: var(--color-primary); }
    .kpi-color-primary::before { background: linear-gradient(90deg, transparent, var(--color-primary), transparent); }

    .kpi-color-info { border-color: rgba(56, 189, 248, 0.2); }
    .kpi-color-info:hover { border-color: rgba(56, 189, 248, 0.4); box-shadow: 0 8px 32px rgba(56, 189, 248, 0.1); }
    .kpi-color-info .kpi-value { color: var(--color-info); }
    .kpi-color-info::before { background: linear-gradient(90deg, transparent, var(--color-info), transparent); }

    .kpi-color-warning { border-color: rgba(251, 191, 36, 0.2); }
    .kpi-color-warning:hover { border-color: rgba(251, 191, 36, 0.4); box-shadow: 0 8px 32px rgba(251, 191, 36, 0.1); }
    .kpi-color-warning .kpi-value { color: var(--color-warning); }
    .kpi-color-warning::before { background: linear-gradient(90deg, transparent, var(--color-warning), transparent); }

    .kpi-color-secondary { border-color: rgba(143, 168, 146, 0.15); }
    .kpi-color-secondary .kpi-value { color: var(--color-text-secondary); }

    /* ── Header ── */
    .kpi-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .kpi-icon {
      font-size: 1rem;
      line-height: 1;
      color: var(--color-text-muted);
      flex-shrink: 0;
    }

    .kpi-label {
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--color-text-muted);
    }

    /* ── Value ── */
    .kpi-value {
      font-family: var(--font-mono);
      font-size: 2rem;
      font-weight: 500;
      color: var(--color-text);
      line-height: 1;
      letter-spacing: -0.02em;
    }

    .kpi-skeleton {
      display: block;
      width: 80px;
      height: 28px;
      background: var(--color-surface-3);
      border-radius: var(--radius-sm);
      animation: shimmer 1.5s ease-in-out infinite;
    }

    @keyframes shimmer {
      0%, 100% { opacity: 0.5; }
      50%       { opacity: 1; }
    }

    /* ── Subtitle ── */
    .kpi-subtitle {
      font-size: 0.72rem;
      color: var(--color-text-muted);
      font-family: var(--font-mono);
    }

    /* ── Trend ── */
    .kpi-trend {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--color-text-secondary);
    }

    .trend-positive { color: var(--color-success); }
    .trend-negative { color: var(--color-danger); }

    .trend-label {
      font-size: 0.7rem;
      font-weight: 400;
      color: var(--color-text-muted);
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
      .kpi-card { padding: 1rem; }
      .kpi-value { font-size: 1.5rem; }
    }
  `],
})
export class KpiCardComponent {
  /** Etiqueta del KPI */
  @Input() label = '';

  /** Valor numérico — null muestra skeleton */
  @Input() value: number | null = null;

  /** Ícono Unicode o emoji */
  @Input() icon = '◈';

  /** Texto descriptivo bajo el valor */
  @Input() subtitle = '';

  /** Variante de color */
  @Input() color: 'primary' | 'secondary' | 'info' | 'warning' = 'primary';

  /** Tendencia: "+5%", "-2.3%" */
  @Input() trend: string | null = null;

  /** Label secundario para la tendencia */
  @Input() trendLabel: string | null = null;

  /** true=verde, false=rojo, null=neutro */
  @Input() trendPositive: boolean | null = null;

  get trendClass(): string {
    if (this.trendPositive === true)  return 'kpi-trend trend-positive';
    if (this.trendPositive === false) return 'kpi-trend trend-negative';
    return 'kpi-trend';
  }
}
