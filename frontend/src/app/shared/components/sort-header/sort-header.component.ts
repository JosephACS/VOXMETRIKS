/**
 * SortHeaderComponent
 * ===================
 * Encabezado de columna con indicador visual de ordenamiento.
 * Emite evento (sortChange) al hacer clic.
 *
 * Uso:
 *   <app-sort-header
 *     columnKey="nombre_artista"
 *     label="Artista"
 *     [sort]="currentSort()"
 *     (sortChange)="onSort($event)"
 *   />
 */

import {
  Component,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
} from '@angular/core';
import { SortState, SortDirection } from '../../models/table.models';

@Component({
  selector: 'app-sort-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      class="sort-header"
      [class.active]="isActive"
      [class.asc]="isActive && currentDirection === 'asc'"
      [class.desc]="isActive && currentDirection === 'desc'"
      [attr.aria-sort]="ariaSort"
      (click)="toggle()"
      type="button"
    >
      <span class="sort-label">{{ label }}</span>
      <span class="sort-icon" aria-hidden="true">
        @if (!isActive) {
          <span class="sort-arrows">⇅</span>
        } @else if (currentDirection === 'asc') {
          <span class="sort-arrow-active">↑</span>
        } @else {
          <span class="sort-arrow-active">↓</span>
        }
      </span>
    </button>
  `,
  styles: [`
    .sort-header {
      display: inline-flex;
      align-items: center;
      gap: 0.375rem;
      background: none;
      border: none;
      padding: 0;
      cursor: pointer;
      color: inherit;
      font: inherit;
      font-size: inherit;
      font-weight: inherit;
      letter-spacing: inherit;
      text-transform: inherit;
      white-space: nowrap;
      user-select: none;
      transition: color var(--transition-fast, 0.15s ease);
    }

    .sort-header:hover {
      color: var(--color-primary, #22c55e);
    }

    .sort-header.active {
      color: var(--color-primary, #22c55e);
    }

    .sort-label {
      line-height: 1;
    }

    .sort-icon {
      display: inline-flex;
      align-items: center;
      font-size: 0.7em;
      opacity: 0.5;
      transition: opacity var(--transition-fast, 0.15s ease);
    }

    .sort-header:hover .sort-icon,
    .sort-header.active .sort-icon {
      opacity: 1;
    }

    .sort-arrows {
      color: var(--color-text-muted, #4d5e50);
    }

    .sort-arrow-active {
      color: var(--color-primary, #22c55e);
      font-size: 0.9em;
    }
  `],
})
export class SortHeaderComponent {
  @Input({ required: true }) columnKey!: string;
  @Input({ required: true }) label!: string;
  @Input() sort: SortState | null = null;

  @Output() sortChange = new EventEmitter<SortState>();

  get isActive(): boolean {
    return this.sort?.column === this.columnKey && this.sort?.direction !== null;
  }

  get currentDirection(): SortDirection {
    if (this.sort?.column !== this.columnKey) return null;
    return this.sort?.direction ?? null;
  }

  get ariaSort(): string {
    if (!this.isActive) return 'none';
    return this.currentDirection === 'asc' ? 'ascending' : 'descending';
  }

  toggle(): void {
    const current = this.sort?.column === this.columnKey ? this.sort.direction : null;
    let next: SortDirection;
    if (current === null)    next = 'asc';
    else if (current === 'asc') next = 'desc';
    else                     next = null;

    this.sortChange.emit({ column: this.columnKey, direction: next });
  }
}
