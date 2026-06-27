import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { StatsService } from '../../analytics/services/stats.service';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import { LoadRecord, WarehouseTableMeta, TablePreview } from '../../../shared/models/api.models';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

type TableKind = 'dimension' | 'fact' | 'aggregation' | 'control' | 'application' | 'other';

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule, KpiCardComponent, DataSourceBadgeComponent, TranslatePipe],
  templateUrl: './explorer.component.html',
  styleUrls: ['./explorer.component.css'],
})
export class ExplorerComponent implements OnInit {
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
  pageSize = 8;

  filteredTables = computed(() => {
    const q = this.searchFilter().toLowerCase().trim();
    const list = this.tables();
    if (!q) return list;
    return list.filter((t) => t.name.toLowerCase().includes(q));
  });

  activeTable = computed(() =>
    this.tables().find((t) => t.name === this.selectedTable()) ?? null
  );

  sqlQuery = computed(() => this.preview()?.query ?? 'SELECT * FROM ...');

  previewColumns = computed(() => this.preview()?.columns ?? []);

  totalPages = computed(() => {
    const p = this.preview();
    if (!p) return 1;
    return Math.max(1, Math.ceil(p.total / p.limit));
  });

  pagedRows = computed(() => this.preview()?.rows ?? []);

  kindCounts = computed(() => ({
    dimension: this.tables().filter((t) => t.kind === 'dimension').length,
    fact: this.tables().filter((t) => t.kind === 'fact').length,
    aggregation: this.tables().filter((t) => t.kind === 'aggregation').length,
    total: this.tables().length,
  }));

  constructor(private stats: StatsService, private i18n: I18nService) {}

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
        const first = d?.[0]?.name;
        if (first) {
          this.selectedTable.set(first);
          this.loadPreview(first, 1);
        }
      },
      error: (err) => this.handleRequestError(err, 'No se pudieron cargar las tablas del warehouse.'),
    });
  }

  loadLoads() {
    this.isLoadingLoads.set(true);
    this.loadsError.set('');
    this.stats.getLastLoads(10).subscribe({
      next: (d) => { this.loads.set(d ?? []); this.isLoadingLoads.set(false); },
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
            : 'Acceso restringido: se requiere cuenta admin (ingeniero).',
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
    this.loadPreview(name, 1);
  }

  loadPreview(name: string, page: number) {
    this.isLoadingPreview.set(true);
    this.previewError.set('');
    this.stats.getTablePreview(name, page, this.pageSize).subscribe({
      next: (d) => { this.preview.set(d); this.isLoadingPreview.set(false); },
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

  kindLabel(kind: string): string {
    this.i18n.tick();
    const map: Record<string, string> = {
      dimension: this.i18n.t('explorer.kpi.dimensions'),
      fact: this.i18n.t('explorer.kpi.facts'),
      aggregation: this.i18n.t('explorer.kpi.aggregations'),
      control: 'Control',
      application: 'App',
      other: 'Other',
    };
    return map[kind] ?? kind;
  }

  kindClass(kind: string): string {
    return `kind-${kind}`;
  }

  fmt(n: number): string {
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
    const v = row[col];
    return v != null ? String(v) : '—';
  }
}
