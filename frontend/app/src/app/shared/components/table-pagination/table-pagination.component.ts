/**
 * TablePaginationComponent
 * ========================
 * Paginador reutilizable con navegación completa.
 * Muestra ventana de páginas, primera/última, y resumen.
 *
 * Uso:
 *   <app-table-pagination
 *     [page]="page()"
 *     [totalPages]="totalPages()"
 *     [total]="total()"
 *     [limit]="limit"
 *     entityLabel="artistas"
 *     (pageChange)="goTo($event)"
 *   />
 */

import {
  Component,
  Input,
  Output,
  EventEmitter,
  computed,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-table-pagination',
  standalone: true,
  imports: [DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (totalPages > 1) {
      <div class="pagination">
        <!-- Info -->
        <span class="pagination-info font-mono">
          {{ rangeStart | number }}–{{ rangeEnd | number }}
          <span class="pagination-sep">de</span>
          {{ total | number }} {{ entityLabel }}
        </span>

        <!-- Controls -->
        <div class="pagination-controls" role="navigation" [attr.aria-label]="'Paginación ' + entityLabel">

          <!-- First -->
          <button
            class="pagination-btn"
            [disabled]="page <= 1"
            (click)="emit(1)"
            title="Primera página"
            aria-label="Primera página"
          >«</button>

          <!-- Prev -->
          <button
            class="pagination-btn"
            [disabled]="page <= 1"
            (click)="emit(page - 1)"
            title="Página anterior"
            aria-label="Página anterior"
          >‹</button>

          <!-- Page window -->
          @for (p of pageWindow; track p) {
            @if (p === -1) {
              <span class="pagination-ellipsis">…</span>
            } @else {
              <button
                class="pagination-btn"
                [class.active]="p === page"
                [attr.aria-current]="p === page ? 'page' : null"
                (click)="emit(p)"
              >{{ p }}</button>
            }
          }

          <!-- Next -->
          <button
            class="pagination-btn"
            [disabled]="page >= totalPages"
            (click)="emit(page + 1)"
            title="Página siguiente"
            aria-label="Página siguiente"
          >›</button>

          <!-- Last -->
          <button
            class="pagination-btn"
            [disabled]="page >= totalPages"
            (click)="emit(totalPages)"
            title="Última página"
            aria-label="Última página"
          >»</button>
        </div>
      </div>
    }
  `,
  styles: [`
    .pagination {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.75rem;
      padding: 0.875rem 0;
    }

    .pagination-info {
      font-size: 0.72rem;
      color: var(--color-text-muted);
    }

    .pagination-sep {
      margin: 0 0.2em;
    }

    .pagination-controls {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .pagination-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 32px;
      height: 32px;
      padding: 0 0.5rem;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      color: var(--color-text-secondary);
      font-family: var(--font-mono);
      font-size: 0.78rem;
      cursor: pointer;
      transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
    }

    .pagination-btn:hover:not(:disabled) {
      background: var(--color-surface-2);
      border-color: var(--color-border-hover);
      color: var(--color-text);
    }

    .pagination-btn.active {
      background: var(--color-primary-dark);
      border-color: var(--color-primary);
      color: var(--color-primary);
      font-weight: 600;
    }

    .pagination-btn:disabled {
      opacity: 0.35;
      cursor: not-allowed;
    }

    .pagination-ellipsis {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 24px;
      color: var(--color-text-muted);
      font-size: 0.75rem;
    }

    @media (max-width: 480px) {
      .pagination { justify-content: center; }
      .pagination-info { display: none; }
    }
  `],
})
export class TablePaginationComponent {
  @Input({ required: true }) page!: number;
  @Input({ required: true }) totalPages!: number;
  @Input() total = 0;
  @Input() limit = 50;
  @Input() entityLabel = 'registros';
  /** Número de páginas visibles en la ventana (impar recomendado) */
  @Input() windowSize = 5;

  @Output() pageChange = new EventEmitter<number>();

  get rangeStart(): number {
    return Math.min((this.page - 1) * this.limit + 1, this.total);
  }

  get rangeEnd(): number {
    return Math.min(this.page * this.limit, this.total);
  }

  /** Genera la ventana de páginas con elipsis (-1) */
  get pageWindow(): number[] {
    const total = this.totalPages;
    const current = this.page;
    const half = Math.floor(this.windowSize / 2);

    if (total <= this.windowSize + 2) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }

    const pages: number[] = [];
    let start = Math.max(2, current - half);
    let end   = Math.min(total - 1, current + half);

    // Ajustar para mantener windowSize páginas
    if (end - start < this.windowSize - 1) {
      if (current - half < 2)  end   = Math.min(total - 1, start + this.windowSize - 1);
      else                     start = Math.max(2,          end   - this.windowSize + 1);
    }

    pages.push(1);
    if (start > 2) pages.push(-1); // elipsis izquierda

    for (let i = start; i <= end; i++) pages.push(i);

    if (end < total - 1) pages.push(-1); // elipsis derecha
    pages.push(total);

    return pages;
  }

  emit(p: number): void {
    if (p < 1 || p > this.totalPages || p === this.page) return;
    this.pageChange.emit(p);
  }
}
