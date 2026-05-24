/**
 * KpiCardComponent — Polished v2.1
 * Tarjeta de métrica con skeleton loader, hover microinteraction, y accesibilidad.
 */

import { Component, Input } from '@angular/core';
import { DecimalPipe }      from '@angular/common';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [DecimalPipe],
  template: `
    <div
      class="kpi-card"
      [class]="'kpi-card kpi-color-' + color"
      [attr.role]="'figure'"
      [attr.aria-label]="label + ': ' + (value !== null && value !== undefined ? value : 'cargando')"
    >
      <!-- Accent line top -->
      <div class="kpi-accent" aria-hidden="true"></div>

      <!-- Header -->
      <div class="kpi-header">
        <span class="kpi-icon" aria-hidden="true">{{ icon }}</span>
        <span class="kpi-label">{{ label }}</span>
      </div>

      <!-- Value (or skeleton) -->
      <div class="kpi-value" [attr.aria-live]="'polite'">
        @if (value !== null && value !== undefined) {
          <span class="kpi-value-num">{{ value | number }}</span>
        } @else {
          <span class="kpi-skeleton" aria-label="Cargando..." aria-busy="true"></span>
        }
      </div>

      <!-- Subtitle -->
      @if (subtitle) {
        <div class="kpi-subtitle" aria-label="Fuente: {{ subtitle }}">{{ subtitle }}</div>
      }

      <!-- Trend -->
      @if (trend) {
        <div class="kpi-trend" [class]="trendClass">
          <span class="trend-value">{{ trend }}</span>
          @if (trendLabel) {
            <span class="trend-label">{{ trendLabel }}</span>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .kpi-card {
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      padding: 1.25rem;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      overflow: hidden;
      transition: transform var(--transition), border-color var(--transition), box-shadow var(--transition);
      cursor: default;
    }

    .kpi-card:hover {
      transform: translateY(-3px);
      box-shadow: var(--shadow-md);
    }

    /* ── Accent line ── */
    .kpi-accent {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      opacity: 0;
      transition: opacity var(--transition);
    }

    .kpi-card:hover .kpi-accent { opacity: 1; }

    /* ── Color variants ── */
    .kpi-color-primary {
      border-color: rgba(34, 197, 94, 0.18);
    }
    .kpi-color-primary:hover {
      border-color: rgba(34, 197, 94, 0.35);
      box-shadow: 0 8px 32px rgba(34, 197, 94, 0.09);
    }
    .kpi-color-primary .kpi-value-num { color: var(--color-primary); }
    .kpi-color-primary .kpi-accent {
      background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
    }

    .kpi-color-info {
      border-color: rgba(56, 189, 248, 0.18);
    }
    .kpi-color-info:hover {
      border-color: rgba(56, 189, 248, 0.35);
      box-shadow: 0 8px 32px rgba(56, 189, 248, 0.09);
    }
    .kpi-color-info .kpi-value-num { color: var(--color-info); }
    .kpi-color-info .kpi-accent {
      background: linear-gradient(90deg, transparent, var(--color-info), transparent);
    }

    .kpi-color-warning {
      border-color: rgba(251, 191, 36, 0.18);
    }
    .kpi-color-warning:hover {
      border-color: rgba(251, 191, 36, 0.35);
      box-shadow: 0 8px 32px rgba(251, 191, 36, 0.09);
    }
    .kpi-color-warning .kpi-value-num { color: var(--color-warning); }
    .kpi-color-warning .kpi-accent {
      background: linear-gradient(90deg, transparent, var(--color-warning), transparent);
    }

    .kpi-color-secondary {
      border-color: rgba(143, 168, 146, 0.15);
    }
    .kpi-color-secondary .kpi-value-num { color: var(--color-text-secondary); }
    .kpi-color-secondary .kpi-accent {
      background: linear-gradient(90deg, transparent, var(--color-text-secondary), transparent);
    }

    /* ── Header ── */
    .kpi-header {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .kpi-icon {
      font-size: 0.9rem;
      line-height: 1;
      color: var(--color-text-muted);
      flex-shrink: 0;
    }

    .kpi-label {
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--color-text-muted);
    }

    /* ── Value ── */
    .kpi-value {
      font-family: var(--font-mono);
      font-size: 2rem;
      font-weight: 400;
      line-height: 1;
      letter-spacing: -0.02em;
      min-height: 2rem;
    }

    .kpi-value-num {
      display: block;
      transition: color var(--transition-fast);
    }

    /* ── Skeleton ── */
    .kpi-skeleton {
      display: block;
      width: 80px;
      height: 26px;
      background: linear-gradient(
        90deg,
        var(--color-skeleton-base) 25%,
        var(--color-skeleton-shimmer) 50%,
        var(--color-skeleton-base) 75%
      );
      background-size: 200% 100%;
      border-radius: var(--radius-sm);
      animation: shimmer 1.6s ease-in-out infinite;
    }

    /* ── Subtitle ── */
    .kpi-subtitle {
      font-size: 0.68rem;
      color: var(--color-text-muted);
      font-family: var(--font-mono);
      letter-spacing: 0.02em;
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
      .kpi-value { font-size: 1.625rem; }
    }

    @media (max-width: 480px) {
      .kpi-value { font-size: 1.375rem; }
    }
  `],
})
export class KpiCardComponent {
  @Input() label = '';
  @Input() value: number | null = null;
  @Input() icon = '◈';
  @Input() subtitle = '';
  @Input() color: 'primary' | 'secondary' | 'info' | 'warning' = 'primary';
  @Input() trend: string | null = null;
  @Input() trendLabel: string | null = null;
  @Input() trendPositive: boolean | null = null;

  get trendClass(): string {
    if (this.trendPositive === true)  return 'kpi-trend trend-positive';
    if (this.trendPositive === false) return 'kpi-trend trend-negative';
    return 'kpi-trend';
  }
}
