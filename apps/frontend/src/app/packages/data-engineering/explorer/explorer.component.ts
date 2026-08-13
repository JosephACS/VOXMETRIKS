import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { StatsService } from '../../analytics/services/stats.service';
import { LoadRecord, TablePreview, WarehouseTableMeta } from '../../../shared/models/api.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

const PREFERRED_TABLES = [
  'fact_streaming',
  'fact_user_activity',
  'fact_playlist_activity',
  'fact_favorites',
  'fact_searches',
  'fact_stream_sessions',
  'dim_track',
  'dim_artista',
  'dim_album',
  'dim_usuario',
  'dim_playlist',
  'dim_genero',
  'dim_tiempo',
];

const SENSITIVE_COL_RE =
  /(password|passwd|secret|token|api[_-]?key|auth[_-]?key|private[_-]?key|credential|hash|salt|ssn|session[_-]?id)/i;

const HUMAN_TABLE_NAMES: Record<string, string> = {
  fact_streaming: 'Streams',
  fact_user_activity: 'Actividad de usuario',
  fact_playlist_activity: 'Actividad de playlist',
  fact_favorites: 'Favoritos',
  fact_searches: 'Búsquedas',
  fact_stream_sessions: 'Sesiones',
  dim_track: 'Pistas',
  dim_artista: 'Artistas',
  dim_album: 'Álbumes',
  dim_usuario: 'Usuarios',
  dim_playlist: 'Playlists',
  dim_genero: 'Géneros',
  dim_tiempo: 'Tiempo',
};

const MAX_PREVIEW_COLS = 10;

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './explorer.component.html',
  styleUrls: ['./explorer.component.css'],
})
export class ExplorerComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly stats = inject(StatsService);
  private readonly i18n = inject(I18nService);

  isLoadingTables = signal(true);
  isLoadingPreview = signal(false);
  isLoadingLoads = signal(true);
  hasError = signal(false);
  accessDenied = signal(false);
  errorMessage = signal('');
  previewError = signal('');
  loadsError = signal('');
  loads = signal<LoadRecord[]>([]);
  tables = signal<WarehouseTableMeta[]>([]);
  preview = signal<TablePreview | null>(null);

  selectedTable = signal('');
  searchFilter = signal('');
  page = signal(1);
  pageSize = signal(50);
  showMobileList = signal(true);

  sortedTables = computed(() => {
    const list = [...this.tables()];
    const rank = (name: string): number => {
      const idx = PREFERRED_TABLES.indexOf(name);
      return idx >= 0 ? idx : 1000 + name.charCodeAt(0);
    };
    return list.sort((a, b) => {
      const ra = rank(a.name);
      const rb = rank(b.name);
      if (ra !== rb) return ra - rb;
      return a.name.localeCompare(b.name);
    });
  });

  filteredTables = computed(() => {
    const q = this.searchFilter().toLowerCase().trim();
    const list = this.sortedTables();
    if (!q) return list;
    return list.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        this.humanTableName(t.name).toLowerCase().includes(q) ||
        t.kind.toLowerCase().includes(q),
    );
  });

  activeTable = computed(
    () => this.tables().find((t) => t.name === this.selectedTable()) ?? null,
  );

  schemaColumns = computed(() => this.activeTable()?.columns ?? []);

  previewColumns = computed(() => {
    const cols = this.preview()?.columns ?? [];
    const safe = cols.filter((c) => !this.isSensitiveColumn(c));
    return safe.slice(0, MAX_PREVIEW_COLS);
  });

  hiddenPreviewCols = computed(() => {
    const cols = (this.preview()?.columns ?? []).filter((c) => !this.isSensitiveColumn(c));
    return Math.max(0, cols.length - MAX_PREVIEW_COLS);
  });

  totalPages = computed(() => {
    const p = this.preview();
    if (!p) return 1;
    return Math.max(1, Math.ceil(p.total / p.limit));
  });

  pagedRows = computed(() => this.preview()?.rows ?? []);

  lastLoadLabel = computed(() => {
    const load = this.loads()[0];
    if (!load?.fecha_carga) return null;
    return new Date(load.fecha_carga).toLocaleString('es-ES', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  });

  ngOnInit() {
    this.loadTables();
    this.loadLoads();
  }

  loadTables() {
    this.isLoadingTables.set(true);
    this.hasError.set(false);
    this.accessDenied.set(false);
    this.errorMessage.set('');
    this.stats.getExplorerTables().subscribe({
      next: (d) => {
        this.tables.set(d ?? []);
        this.isLoadingTables.set(false);
        const fromQuery = this.route.snapshot.queryParamMap.get('table');
        const preferred =
          (fromQuery && d?.some((t) => t.name === fromQuery) ? fromQuery : null) ??
          d?.find((t) => t.name === 'fact_streaming')?.name ??
          d?.find((t) => t.kind === 'fact')?.name ??
          d?.[0]?.name;
        if (preferred) {
          this.selectedTable.set(preferred);
          this.showMobileList.set(false);
          this.loadPreview(preferred, 1);
        }
      },
      error: (err) =>
        this.handleRequestError(err, 'No se pudieron cargar las tablas del almacén.'),
    });
  }

  loadLoads() {
    this.isLoadingLoads.set(true);
    this.loadsError.set('');
    this.stats.getLastLoads(10).subscribe({
      next: (d) => {
        this.loads.set(d ?? []);
        this.isLoadingLoads.set(false);
      },
      error: (err) => {
        this.isLoadingLoads.set(false);
        this.loadsError.set(this.errorDetail(err, 'No se pudo cargar el historial de cargas.'));
      },
    });
  }

  retry() {
    this.loadTables();
    this.loadLoads();
  }

  private handleRequestError(err: unknown, fallback: string): void {
    this.isLoadingTables.set(false);
    this.isLoadingPreview.set(false);
    if (err instanceof HttpErrorResponse) {
      if (err.status === 403) {
        this.accessDenied.set(true);
        this.errorMessage.set(
          typeof err.error?.detail === 'string'
            ? err.error.detail
            : 'Acceso restringido: se requiere cuenta de ingeniería.',
        );
        return;
      }
      if (err.status === 401) {
        this.accessDenied.set(true);
        this.errorMessage.set('Sesión expirada o no autenticado. Vuelve a iniciar sesión.');
        return;
      }
    }
    this.hasError.set(true);
    this.errorMessage.set(fallback);
  }

  private errorDetail(err: unknown, fallback: string): string {
    if (err instanceof HttpErrorResponse && typeof err.error?.detail === 'string') {
      return err.error.detail;
    }
    return fallback;
  }

  selectTable(name: string) {
    this.selectedTable.set(name);
    this.page.set(1);
    this.showMobileList.set(false);
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { table: name },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    this.loadPreview(name, 1);
  }

  backToTables() {
    this.showMobileList.set(true);
  }

  setPageSize(size: 50 | 100) {
    this.pageSize.set(size);
    const name = this.selectedTable();
    if (!name) return;
    this.page.set(1);
    this.loadPreview(name, 1);
  }

  loadPreview(name: string, page: number) {
    this.isLoadingPreview.set(true);
    this.previewError.set('');
    this.stats.getTablePreview(name, page, this.pageSize()).subscribe({
      next: (d) => {
        this.preview.set(d);
        this.isLoadingPreview.set(false);
      },
      error: (err) => {
        this.preview.set(null);
        this.isLoadingPreview.set(false);
        if (err instanceof HttpErrorResponse && (err.status === 401 || err.status === 403)) {
          this.handleRequestError(err, 'No se pudo cargar el preview de la tabla.');
          return;
        }
        this.previewError.set(this.errorDetail(err, 'No se pudo cargar el preview de la tabla.'));
      },
    });
  }

  onFilterChange(value: string) {
    this.searchFilter.set(value);
  }

  humanTableName(name: string): string {
    return HUMAN_TABLE_NAMES[name] ?? name.replace(/^(dim_|fact_|agg_)/, '').replace(/_/g, ' ');
  }

  kindLabel(kind: string): string {
    switch (kind) {
      case 'dimension':
        return 'Dimensión';
      case 'fact':
        return 'Hecho';
      case 'aggregation':
        return 'Agregación';
      case 'control':
        return 'Control';
      case 'application':
        return 'Aplicación';
      default:
        return kind || 'Tabla';
    }
  }

  humanType(type: string): string {
    const t = (type || '').toUpperCase();
    if (!t) return '—';
    if (t.includes('VARCHAR') || t.includes('TEXT') || t.includes('STRING')) return type;
    if (t.includes('INT') || t.includes('BIGINT') || t.includes('HUGEINT')) return type;
    if (t.includes('DOUBLE') || t.includes('FLOAT') || t.includes('DECIMAL') || t.includes('NUMERIC'))
      return type;
    if (t.includes('BOOL')) return type;
    if (t.includes('TIMESTAMP') || t.includes('DATE') || t.includes('TIME')) return type;
    return type;
  }

  isSensitiveColumn(name: string): boolean {
    return SENSITIVE_COL_RE.test(name);
  }

  fmt(n?: number | null): string {
    if (n == null) return '—';
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toLocaleString('es-ES');
  }

  goPage(p: number) {
    const name = this.selectedTable();
    if (!name || p < 1 || p > this.totalPages()) return;
    this.page.set(p);
    this.loadPreview(name, p);
  }

  cellValue(row: Record<string, unknown>, col: string): string {
    if (this.isSensitiveColumn(col)) return '••••';
    const v = row[col];
    if (v == null) return '—';
    const s = String(v);
    return s.length > 80 ? `${s.slice(0, 77)}…` : s;
  }

  loadStatusLabel(estado?: string | null): string {
    const e = (estado || '').toLowerCase();
    if (e === 'ok') return 'OK';
    if (!e) return '—';
    return estado!;
  }
}
