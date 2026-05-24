/**
 * TableSearchComponent
 * ====================
 * Barra de búsqueda reutilizable con debounce integrado.
 * Compatible con todos los feature components del sistema.
 *
 * Uso:
 *   <app-table-search
 *     placeholder="Buscar artista..."
 *     [total]="total()"
 *     entityLabel="artistas"
 *     (searchChange)="onSearch($event)"
 *   />
 */

import {
  Component,
  Input,
  Output,
  EventEmitter,
  signal,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';

@Component({
  selector: 'app-table-search',
  standalone: true,
  imports: [FormsModule, DecimalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="search-bar" [class.has-value]="value().length > 0">
      <span class="search-icon" aria-hidden="true">⌕</span>

      <input
        class="search-input"
        type="search"
        [placeholder]="placeholder"
        [value]="value()"
        (input)="onInput($any($event.target).value)"
        (keydown.escape)="clear()"
        [attr.aria-label]="placeholder"
        autocomplete="off"
        spellcheck="false"
      />

      @if (value().length > 0) {
        <button
          class="clear-btn"
          type="button"
          aria-label="Limpiar búsqueda"
          (click)="clear()"
        >×</button>
      }

      @if (showCount && total !== null) {
        <span class="search-count font-mono">
          @if (value().length > 0) {
            {{ total | number }} resultado{{ total !== 1 ? 's' : '' }}
          } @else {
            {{ total | number }} {{ entityLabel }}
          }
        </span>
      }
    </div>
  `,
  styles: [`
    .search-bar {
      display: flex;
      align-items: center;
      gap: 0.625rem;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 0 1rem;
      margin-bottom: 1rem;
      transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
    }

    .search-bar:focus-within {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px var(--color-primary-glow);
    }

    .search-icon {
      font-size: 1.15rem;
      color: var(--color-text-muted);
      flex-shrink: 0;
      user-select: none;
    }

    .search-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--color-text);
      font-family: var(--font-body);
      font-size: 0.9rem;
      padding: 0.75rem 0;
      min-width: 0;
    }

    .search-input::placeholder {
      color: var(--color-text-muted);
    }

    /* Remove native search clear button */
    .search-input::-webkit-search-cancel-button { display: none; }

    .clear-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      background: var(--color-surface-3);
      border: 1px solid var(--color-border);
      border-radius: 50%;
      cursor: pointer;
      color: var(--color-text-muted);
      font-size: 0.85rem;
      line-height: 1;
      flex-shrink: 0;
      transition: background var(--transition-fast), color var(--transition-fast);
    }

    .clear-btn:hover {
      background: var(--color-surface-2);
      color: var(--color-text);
    }

    .search-count {
      font-size: 0.72rem;
      color: var(--color-text-muted);
      white-space: nowrap;
      flex-shrink: 0;
    }

    @media (max-width: 480px) {
      .search-count { display: none; }
    }
  `],
})
export class TableSearchComponent implements OnInit, OnDestroy {
  @Input() placeholder = 'Buscar...';
  @Input() debounce = 350;
  @Input() total: number | null = null;
  @Input() entityLabel = 'registros';
  @Input() showCount = true;
  /** Valor inicial pre-cargado */
  @Input() set initialValue(v: string) { this.value.set(v); }

  @Output() searchChange = new EventEmitter<string>();

  protected readonly value = signal('');

  private readonly input$ = new Subject<string>();
  private readonly destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.input$.pipe(
      debounceTime(this.debounce),
      distinctUntilChanged(),
      takeUntil(this.destroy$),
    ).subscribe(term => this.searchChange.emit(term));
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  protected onInput(v: string): void {
    this.value.set(v);
    this.input$.next(v);
  }

  protected clear(): void {
    this.value.set('');
    this.input$.next('');
  }
}
