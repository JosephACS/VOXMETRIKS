/**
 * EmptyStateComponent
 * ===================
 * Estado vacío reutilizable para tablas analíticas.
 * Soporta: sin-datos, sin-resultados, error, cargando.
 *
 * Uso:
 *   <app-empty-state
 *     type="no-results"
 *     [searchTerm]="searchVal()"
 *     (clearSearch)="onClearSearch()"
 *   />
 */

import {
  Component,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
} from '@angular/core';

export type EmptyStateType = 'no-data' | 'no-results' | 'error' | 'loading';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="empty-state" [class]="'empty-type-' + type">
      <div class="empty-icon" aria-hidden="true">{{ icon }}</div>
      <div class="empty-title">{{ title }}</div>
      @if (description) {
        <p class="empty-description">{{ description }}</p>
      }
      @if (type === 'no-results' && searchTerm) {
        <p class="empty-term">Búsqueda: "<strong>{{ searchTerm }}</strong>"</p>
        <button class="empty-action-btn" type="button" (click)="clearSearch.emit()">
          Limpiar búsqueda
        </button>
      }
      @if (type === 'error') {
        <button class="empty-action-btn" type="button" (click)="retry.emit()">
          Reintentar
        </button>
      }
    </div>
  `,
  styles: [`
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 3.5rem 1.5rem;
      text-align: center;
    }

    .empty-icon {
      font-size: 2.5rem;
      line-height: 1;
      margin-bottom: 0.25rem;
      opacity: 0.5;
    }

    .empty-title {
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--color-text-secondary);
    }

    .empty-description {
      font-size: 0.78rem;
      color: var(--color-text-muted);
      max-width: 320px;
    }

    .empty-term {
      font-size: 0.78rem;
      color: var(--color-text-muted);
    }

    .empty-term strong {
      color: var(--color-text-secondary);
    }

    .empty-type-error .empty-icon { opacity: 0.7; }
    .empty-type-error .empty-title { color: var(--color-danger); }

    .empty-action-btn {
      margin-top: 0.5rem;
      padding: 0.4rem 0.875rem;
      background: var(--color-surface-2);
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      color: var(--color-text-secondary);
      font-family: var(--font-body);
      font-size: 0.78rem;
      cursor: pointer;
      transition: border-color var(--transition-fast), color var(--transition-fast);
    }

    .empty-action-btn:hover {
      border-color: var(--color-primary);
      color: var(--color-primary);
    }
  `],
})
export class EmptyStateComponent {
  @Input() type: EmptyStateType = 'no-data';
  @Input() searchTerm = '';
  @Input() customTitle?: string;
  @Input() customDescription?: string;

  @Output() clearSearch = new EventEmitter<void>();
  @Output() retry = new EventEmitter<void>();

  get icon(): string {
    switch (this.type) {
      case 'no-results': return '⌕';
      case 'error':      return '⚠';
      case 'loading':    return '◌';
      default:           return '◈';
    }
  }

  get title(): string {
    if (this.customTitle) return this.customTitle;
    switch (this.type) {
      case 'no-results': return 'Sin resultados';
      case 'error':      return 'Error al cargar datos';
      case 'loading':    return 'Cargando...';
      default:           return 'Sin datos disponibles';
    }
  }

  get description(): string {
    if (this.customDescription) return this.customDescription;
    switch (this.type) {
      case 'no-results': return 'Intenta con un término diferente o quita los filtros activos.';
      case 'error':      return 'No se pudo conectar con el servidor. Verifica la conexión.';
      default:           return '';
    }
  }
}
