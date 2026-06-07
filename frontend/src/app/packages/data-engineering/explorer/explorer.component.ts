import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StatsService } from '../../analytics/services/stats.service';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import { LoadRecord, WarehouseTableMeta, TablePreview } from '../../../shared/models/api.models';

type TableKind = 'dimension' | 'fact' | 'aggregation' | 'control' | 'application' | 'other';

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule, KpiCardComponent],
  templateUrl: './explorer.component.html',
  styleUrls: ['./explorer.component.css'],
})
export class ExplorerComponent implements OnInit {
  isLoadingTables = signal(true);
  isLoadingPreview = signal(false);
  isLoadingLoads = signal(true);
  hasError = signal(false);
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

  constructor(private stats: StatsService) {}

  ngOnInit() {
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
      error: () => {
        this.hasError.set(true);
        this.isLoadingTables.set(false);
      },
    });

    this.stats.getLastLoads(10).subscribe({
      next: (d) => { this.loads.set(d ?? []); this.isLoadingLoads.set(false); },
      error: () => { this.hasError.set(true); this.isLoadingLoads.set(false); },
    });
  }

  selectTable(name: string) {
    this.selectedTable.set(name);
    this.page.set(1);
    this.loadPreview(name, 1);
  }

  loadPreview(name: string, page: number) {
    this.isLoadingPreview.set(true);
    this.stats.getTablePreview(name, page, this.pageSize).subscribe({
      next: (d) => { this.preview.set(d); this.isLoadingPreview.set(false); },
      error: () => { this.preview.set(null); this.isLoadingPreview.set(false); },
    });
  }

  onFilterChange(value: string) {
    this.searchFilter.set(value);
  }

  kindLabel(kind: string): string {
    const map: Record<string, string> = {
      dimension: 'Dimensión', fact: 'Hecho', aggregation: 'Agregación',
      control: 'Control', application: 'App', other: 'Otro',
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
