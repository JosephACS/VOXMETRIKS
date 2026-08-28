/**
 * KpiCardComponent — Polished v2.1
 * Tarjeta de métrica con skeleton loader, hover microinteraction, y accesibilidad.
 */

import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject, input, effect, signal } from '@angular/core';
import { DecimalPipe }      from '@angular/common';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [DecimalPipe, TranslatePipe],
  template: `
    <div
      class="kpi-card"
      [class]="'kpi-card kpi-color-' + color()"
      [attr.role]="'figure'"
      [attr.title]="tooltip() || null"
      [attr.aria-label]="(tooltip() || label()) + ': ' + (value() !== null && value() !== undefined ? value() : ('common.loading' | t))"
    >
      <!-- Accent line top -->
      <div class="kpi-accent" aria-hidden="true"></div>

      <!-- Header -->
      <div class="kpi-header">
        <span class="kpi-icon icon-wrap-md" [innerHTML]="iconSvg" aria-hidden="true"></span>
        <span class="kpi-label">{{ label() }}</span>
        @if (note()) {
          <span class="kpi-note" [attr.title]="noteTip() || null">{{ note() }}</span>
        }
      </div>

      <!-- Value (or skeleton) -->
      <div class="kpi-value" [attr.aria-live]="'polite'">
        @if (displayValue() !== null && displayValue() !== undefined) {
          <span class="kpi-value-num">{{ displayValue() | number }}</span>
        } @else {
          <span class="kpi-skeleton" [attr.aria-label]="'common.loading' | t" aria-busy="true"></span>
        }
      </div>

      <!-- Subtitle -->
      @if (subtitle()) {
        <div class="kpi-subtitle" aria-label="Fuente: {{ subtitle() }}">{{ subtitle() }}</div>
      }

      <!-- Trend -->
      @if (trend()) {
        <div class="kpi-trend" [class]="trendClass">
          <span class="trend-value">{{ trend() }}</span>
          @if (trendLabel()) {
            <span class="trend-label">{{ trendLabel() }}</span>
          }
          @if (trendNote()) {
            <span class="trend-note" [attr.title]="trendNoteTip() || null">{{ trendNote() }}</span>
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
      gap: 0.35rem;
      padding: 0.875rem 1rem;
      background: var(--spotify-card);
      backdrop-filter: none;
      -webkit-backdrop-filter: none;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      transition: transform var(--motion-duration-fast) var(--motion-ease-standard),
        border-color var(--motion-duration-fast) var(--motion-ease-standard),
        box-shadow var(--motion-duration-fast) var(--motion-ease-standard);
      cursor: default;
      box-shadow: var(--shadow-sm);
    }

    .kpi-card:hover {
      transform: translateY(-2px);
      background: var(--spotify-card-hover);
      box-shadow: var(--shadow-glow);
      border-color: var(--color-border-hover);
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
      border-color: rgba(232, 163, 61, 0.18);
    }
    .kpi-color-primary:hover {
      border-color: rgba(232, 163, 61, 0.35);
      box-shadow: 0 8px 32px rgba(232, 163, 61, 0.12);
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
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      color: var(--color-text-muted);
      flex-shrink: 0;
      opacity: 0.85;
    }

    .kpi-icon :deep(svg) { width: 16px; height: 16px; }

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
      font-size: 1.625rem;
      font-weight: 600;
      line-height: 1;
      letter-spacing: -0.02em;
      min-height: 1.625rem;
    }

    .kpi-value-num {
      display: block;
      transition: color var(--motion-duration-fast) var(--motion-ease-standard);
      font-variant-numeric: tabular-nums;
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
      animation: vm-shimmer 1.6s var(--motion-ease-in-out) infinite;
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

    /* ── Origen del dato (discreto) ── */
    .kpi-note,
    .trend-note {
      font-size: 0.56rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      padding: 1px 7px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--color-text-muted);
      cursor: help;
      white-space: nowrap;
    }

    .kpi-note { margin-left: auto; }

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
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);

  displayValue = signal<number | null>(null);

  constructor() {
    effect((onCleanup) => {
      const target = this.value();
      if (target == null) {
        this.displayValue.set(null);
        return;
      }
      const from = this.displayValue() ?? 0;
      const start = performance.now();
      const duration = 480;
      let frame = 0;
      const step = (now: number) => {
        const progress = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        this.displayValue.set(Math.round(from + (target - from) * eased));
        if (progress < 1) {
          frame = requestAnimationFrame(step);
        }
      };
      frame = requestAnimationFrame(step);
      onCleanup(() => cancelAnimationFrame(frame));
    });
  }

  readonly label = input('');
  readonly value = input<number | null>(null);
  readonly iconKey = input('chart');
  readonly subtitle = input('');
  readonly color = input<'primary' | 'secondary' | 'info' | 'warning'>('primary');
  readonly trend = input<string | null>(null);
  readonly trendLabel = input<string | null>(null);
  readonly trendPositive = input<boolean | null>(null);
  readonly tooltip = input('');
  readonly note = input<string | null>(null);
  readonly noteTip = input<string | null>(null);
  readonly trendNote = input<string | null>(null);
  readonly trendNoteTip = input<string | null>(null);

  get iconSvg(): SafeHtml {
    return this.iconRender.render(this.iconKey(), 16);
  }

  get trendClass(): string {
    if (this.trendPositive() === true)  return 'kpi-trend trend-positive';
    if (this.trendPositive() === false) return 'kpi-trend trend-negative';
    return 'kpi-trend';
  }
}
