/**
 * VOXMETRIK_V2 — Table & Filter Models
 *
 * Tipos compartidos para el sistema de tablas analíticas reutilizables.
 * Todos los componentes de tabla, filtro y paginación usan estos contratos.
 */

// ═══════════════════════════════════════════════════════════════════════════
// SORTING
// ═══════════════════════════════════════════════════════════════════════════

export type SortDirection = 'asc' | 'desc' | null;

export interface SortState {
  column: string;
  direction: SortDirection;
}

// ═══════════════════════════════════════════════════════════════════════════
// TABLE COLUMNS
// ═══════════════════════════════════════════════════════════════════════════

export interface TableColumn<T = any> {
  /** Clave de propiedad en el objeto de datos */
  key: string;
  /** Etiqueta visible en el encabezado */
  label: string;
  /** Permite ordenar esta columna */
  sortable?: boolean;
  /** Ancho fijo opcional (CSS string: '80px', '10%') */
  width?: string;
  /** Ancho mínimo en tablas con scroll horizontal */
  minWidth?: string;
  /** Alineación del contenido */
  align?: 'left' | 'center' | 'right';
  /** Clase CSS adicional para las celdas */
  cellClass?: string;
  /** Función de formato para mostrar el valor */
  format?: (value: any, row: T) => string;
  /** Tipo especial de celda */
  type?: 'text' | 'number' | 'mono' | 'badge' | 'bar' | 'duration' | 'spotify' | 'explicit';
  /** Config extra para tipo 'bar' */
  barMax?: number;
  /** Color del bar (CSS var o hex) */
  barColor?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// PAGINATION
// ═══════════════════════════════════════════════════════════════════════════

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface PageChangeEvent {
  page: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// FILTERS
// ═══════════════════════════════════════════════════════════════════════════

export interface FilterOption {
  value: string | number;
  label: string;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'range' | 'toggle';
  options?: FilterOption[];
  /** Para tipo range */
  min?: number;
  max?: number;
  step?: number;
  /** Sufijo para mostrar el valor (ej. '%') */
  suffix?: string;
}

export interface ActiveFilter {
  key: string;
  value: string | number | boolean | [number, number];
}

export interface FilterState {
  search: string;
  filters: ActiveFilter[];
  sort: SortState;
  page: number;
  limit: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// TABLE STATE
// ═══════════════════════════════════════════════════════════════════════════

export type TableLoadingState = 'idle' | 'loading' | 'success' | 'error' | 'empty';

export interface TableState<T> {
  data: T[];
  loading: TableLoadingState;
  pagination: PaginationState;
  sort: SortState;
  search: string;
  error?: string;
}
