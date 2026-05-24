/**
 * TableSkeletonComponent
 * ======================
 * Filas skeleton con animación shimmer para estados de carga en tablas.
 *
 * Uso:
 *   <app-table-skeleton [rows]="10" [columns]="6" />
 */

import {
  Component,
  Input,
  ChangeDetectionStrategy,
  computed,
  signal,
} from '@angular/core';

@Component({
  selector: 'app-table-skeleton',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @for (row of rowArray; track row) {
      <tr class="skeleton-row">
        @for (col of colArray; track col) {
          <td class="skeleton-cell">
            <div
              class="skeleton-line"
              [style.width]="getWidth(col)"
            ></div>
          </td>
        }
      </tr>
    }
  `,
  styles: [`
    .skeleton-row {
      animation: none;
    }

    .skeleton-cell {
      padding: 0.75rem 1rem;
    }

    .skeleton-line {
      height: 12px;
      background: linear-gradient(
        90deg,
        var(--color-surface-2) 25%,
        var(--color-surface-3) 50%,
        var(--color-surface-2) 75%
      );
      background-size: 200% 100%;
      border-radius: var(--radius-sm);
      animation: shimmer 1.6s ease-in-out infinite;
    }

    @keyframes shimmer {
      0%   { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Stagger animation delay per row */
    .skeleton-row:nth-child(1) .skeleton-line { animation-delay: 0s; }
    .skeleton-row:nth-child(2) .skeleton-line { animation-delay: 0.08s; }
    .skeleton-row:nth-child(3) .skeleton-line { animation-delay: 0.16s; }
    .skeleton-row:nth-child(4) .skeleton-line { animation-delay: 0.24s; }
    .skeleton-row:nth-child(5) .skeleton-line { animation-delay: 0.32s; }
    .skeleton-row:nth-child(6) .skeleton-line { animation-delay: 0.40s; }
    .skeleton-row:nth-child(7) .skeleton-line { animation-delay: 0.48s; }
    .skeleton-row:nth-child(8) .skeleton-line { animation-delay: 0.56s; }
  `],
})
export class TableSkeletonComponent {
  @Input() rows = 8;
  @Input() columns = 5;
  /** Widths per column index (looped if shorter than columns) */
  @Input() widths: string[] = ['40px', '60%', '80px', '100px', '70px'];

  get rowArray(): number[] {
    return Array.from({ length: this.rows }, (_, i) => i);
  }

  get colArray(): number[] {
    return Array.from({ length: this.columns }, (_, i) => i);
  }

  getWidth(colIndex: number): string {
    if (!this.widths.length) return '60%';
    return this.widths[colIndex % this.widths.length];
  }
}
