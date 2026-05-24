/**
 * TableFilterComponent
 * ====================
 * Panel de filtros reutilizable con chips, select y rangos.
 * Emite (filterChange) al cambiar cualquier filtro.
 *
 * Uso:
 *   <app-table-filter
 *     [configs]="filterConfigs"
 *     [active]="activeFilters()"
 *     (filterChange)="onFilter($event)"
 *     (clearAll)="onClearFilters()"
 *   />
 */

import {
  Component,
  Input,
  Output,
  EventEmitter,
  signal,
  computed,
  OnChanges,
  SimpleChanges,
  ChangeDetectionStrategy,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActiveFilter, FilterConfig, FilterOption } from '../../models/table.models';

@Component({
  selector: 'app-table-filter',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="filter-bar">
      <!-- Filter chips row -->
      <div class="filter-chips-row">

        <!-- Toggle button -->
        <button
          class="filter-toggle-btn"
          [class.active]="panelOpen()"
          type="button"
          (click)="togglePanel()"
          [attr.aria-expanded]="panelOpen()"
        >
          <span class="filter-icon">⊟</span>
          Filtros
          @if (activeCount() > 0) {
            <span class="filter-badge">{{ activeCount() }}</span>
          }
        </button>

        <!-- Active filter chips -->
        @for (chip of activeChips(); track chip.key) {
          <div class="filter-chip">
            <span class="chip-label">{{ chip.label }}: {{ chip.display }}</span>
            <button
              class="chip-remove"
              type="button"
              (click)="removeFilter(chip.key)"
              [attr.aria-label]="'Quitar filtro ' + chip.label"
            >×</button>
          </div>
        }

        @if (activeCount() > 0) {
          <button class="clear-all-btn" type="button" (click)="clearAll()">
            Limpiar todo
          </button>
        }
      </div>

      <!-- Filter panel -->
      @if (panelOpen()) {
        <div class="filter-panel" role="region" aria-label="Opciones de filtro">
          @for (config of configs; track config.key) {
            <div class="filter-field">
              <label class="filter-label" [attr.for]="'filter-' + config.key">
                {{ config.label }}
              </label>

              @if (config.type === 'select') {
                <select
                  class="filter-select"
                  [id]="'filter-' + config.key"
                  [ngModel]="getSelectValue(config.key)"
                  (ngModelChange)="onSelect(config.key, $event)"
                >
                  <option value="">Todos</option>
                  @for (opt of config.options ?? []; track opt.value) {
                    <option [value]="opt.value">{{ opt.label }}</option>
                  }
                </select>
              }

              @if (config.type === 'toggle') {
                <label class="filter-toggle" [attr.for]="'filter-' + config.key">
                  <input
                    type="checkbox"
                    [id]="'filter-' + config.key"
                    [ngModel]="getToggleValue(config.key)"
                    (ngModelChange)="onToggle(config.key, $event)"
                    class="toggle-input"
                  />
                  <span class="toggle-track">
                    <span class="toggle-thumb"></span>
                  </span>
                </label>
              }

              @if (config.type === 'range') {
                <div class="range-wrapper">
                  <span class="range-val font-mono">{{ getRangeValue(config.key) }}{{ config.suffix ?? '' }}</span>
                  <input
                    type="range"
                    class="filter-range"
                    [id]="'filter-' + config.key"
                    [min]="config.min ?? 0"
                    [max]="config.max ?? 100"
                    [step]="config.step ?? 1"
                    [ngModel]="getRangeValue(config.key)"
                    (ngModelChange)="onRange(config.key, $event)"
                  />
                </div>
              }
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .filter-bar {
      margin-bottom: 1rem;
    }

    /* ── Chips row ── */
    .filter-chips-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .filter-toggle-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.375rem;
      padding: 0.4rem 0.75rem;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      color: var(--color-text-secondary);
      font-family: var(--font-body);
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
    }

    .filter-toggle-btn:hover {
      border-color: var(--color-border-hover);
      color: var(--color-text);
    }

    .filter-toggle-btn.active {
      background: var(--color-primary-dark);
      border-color: var(--color-primary);
      color: var(--color-primary);
    }

    .filter-icon {
      font-size: 0.9em;
    }

    .filter-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 18px;
      height: 18px;
      padding: 0 4px;
      background: var(--color-primary);
      border-radius: 9px;
      color: var(--color-bg);
      font-size: 0.65rem;
      font-weight: 700;
      line-height: 1;
    }

    /* ── Active chips ── */
    .filter-chip {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.25rem 0.5rem 0.25rem 0.625rem;
      background: var(--color-primary-dark);
      border: 1px solid rgba(34,197,94,0.3);
      border-radius: 999px;
      font-size: 0.72rem;
      color: var(--color-primary);
    }

    .chip-label {
      white-space: nowrap;
    }

    .chip-remove {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      background: rgba(34,197,94,0.15);
      border: none;
      border-radius: 50%;
      cursor: pointer;
      color: var(--color-primary);
      font-size: 0.75rem;
      line-height: 1;
      transition: background var(--transition-fast);
    }

    .chip-remove:hover {
      background: rgba(34,197,94,0.3);
    }

    .clear-all-btn {
      background: none;
      border: none;
      color: var(--color-text-muted);
      font-size: 0.72rem;
      cursor: pointer;
      padding: 0.25rem;
      text-decoration: underline;
      transition: color var(--transition-fast);
    }

    .clear-all-btn:hover {
      color: var(--color-danger);
    }

    /* ── Filter panel ── */
    .filter-panel {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-top: 0.75rem;
      padding: 1rem 1.25rem;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      animation: slideDown 0.15s ease;
    }

    @keyframes slideDown {
      from { opacity: 0; transform: translateY(-6px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .filter-field {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
      min-width: 140px;
      flex: 1;
    }

    .filter-label {
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--color-text-muted);
    }

    .filter-select {
      background: var(--color-surface-2);
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      color: var(--color-text);
      font-family: var(--font-body);
      font-size: 0.82rem;
      padding: 0.45rem 0.65rem;
      cursor: pointer;
      outline: none;
      transition: border-color var(--transition-fast);
    }

    .filter-select:focus {
      border-color: var(--color-primary);
    }

    /* ── Toggle ── */
    .filter-toggle {
      display: inline-flex;
      align-items: center;
      cursor: pointer;
    }

    .toggle-input {
      position: absolute;
      opacity: 0;
      width: 0;
      height: 0;
    }

    .toggle-track {
      position: relative;
      width: 36px;
      height: 20px;
      background: var(--color-surface-3);
      border: 1px solid var(--color-border);
      border-radius: 10px;
      transition: background var(--transition-fast), border-color var(--transition-fast);
    }

    .toggle-input:checked + .toggle-track {
      background: var(--color-primary-dark);
      border-color: var(--color-primary);
    }

    .toggle-thumb {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      background: var(--color-text-muted);
      border-radius: 50%;
      transition: transform var(--transition-fast), background var(--transition-fast);
    }

    .toggle-input:checked + .toggle-track .toggle-thumb {
      transform: translateX(16px);
      background: var(--color-primary);
    }

    /* ── Range ── */
    .range-wrapper {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .range-val {
      font-size: 0.72rem;
      color: var(--color-primary);
      min-width: 32px;
      text-align: right;
    }

    .filter-range {
      flex: 1;
      -webkit-appearance: none;
      height: 4px;
      background: var(--color-surface-3);
      border-radius: 2px;
      outline: none;
      cursor: pointer;
    }

    .filter-range::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: var(--color-primary);
      cursor: pointer;
      transition: transform var(--transition-fast);
    }

    .filter-range::-webkit-slider-thumb:hover {
      transform: scale(1.2);
    }
  `],
})
export class TableFilterComponent implements OnChanges {
  @Input({ required: true }) configs: FilterConfig[] = [];
  @Input() active: ActiveFilter[] = [];

  @Output() filterChange = new EventEmitter<ActiveFilter[]>();
  @Output() clearAll = new EventEmitter<void>();

  protected readonly panelOpen = signal(false);
  protected readonly internalFilters = signal<ActiveFilter[]>([]);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['active']) {
      this.internalFilters.set([...(this.active ?? [])]);
    }
  }

  protected readonly activeCount = computed(() =>
    this.internalFilters().length
  );

  protected readonly activeChips = computed(() =>
    this.internalFilters().map(f => {
      const cfg = this.configs.find(c => c.key === f.key);
      let display = String(f.value);
      if (cfg?.type === 'select' && cfg.options) {
        const opt = cfg.options.find(o => String(o.value) === String(f.value));
        if (opt) display = opt.label;
      }
      if (cfg?.type === 'toggle') display = f.value ? 'Sí' : 'No';
      if (cfg?.type === 'range') display = `${f.value}${cfg.suffix ?? ''}`;
      return { key: f.key, label: cfg?.label ?? f.key, display };
    })
  );

  protected togglePanel(): void {
    this.panelOpen.update(v => !v);
  }

  protected getSelectValue(key: string): string {
    const f = this.internalFilters().find(f => f.key === key);
    return f ? String(f.value) : '';
  }

  protected getToggleValue(key: string): boolean {
    const f = this.internalFilters().find(f => f.key === key);
    return f ? Boolean(f.value) : false;
  }

  protected getRangeValue(key: string): number {
    const f = this.internalFilters().find(f => f.key === key);
    const cfg = this.configs.find(c => c.key === key);
    return f ? Number(f.value) : (cfg?.min ?? 0);
  }

  protected onSelect(key: string, value: string): void {
    this.setFilter(key, value === '' ? null : value);
  }

  protected onToggle(key: string, value: boolean): void {
    this.setFilter(key, value ? true : null);
  }

  protected onRange(key: string, value: number): void {
    const cfg = this.configs.find(c => c.key === key);
    this.setFilter(key, value === cfg?.min ? null : value);
  }

  protected removeFilter(key: string): void {
    this.setFilter(key, null);
  }

  private setFilter(key: string, value: string | number | boolean | null): void {
    const current = this.internalFilters().filter(f => f.key !== key);
    const updated = value !== null && value !== ''
      ? [...current, { key, value }]
      : current;
    this.internalFilters.set(updated);
    this.filterChange.emit(updated);
  }

  protected clearAll(): void {
    this.internalFilters.set([]);
    this.clearAll.emit();
    this.filterChange.emit([]);
  }
}
