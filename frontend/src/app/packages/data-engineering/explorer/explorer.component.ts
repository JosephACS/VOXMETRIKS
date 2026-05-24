import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StatsService } from '../../analytics/services/stats.service';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import { LoadRecord } from '../../../shared/models/api.models';

type TableKind = 'dimension' | 'fact' | 'aggregation';

interface TableColumn {
  name: string;
  type: string;
}

interface WarehouseTable {
  name: string;
  kind: TableKind;
  layer: 'gold' | 'warehouse';
  rowCount: number;
  lastUpdated: string;
  columns: TableColumn[];
  previewRows: Record<string, string | number>[];
}

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule, KpiCardComponent],
  templateUrl: './explorer.component.html',
  styleUrls: ['./explorer.component.css'],
})
export class ExplorerComponent implements OnInit {
  isLoadingLoads = signal(true);
  hasError = signal(false);
  loads = signal<LoadRecord[]>([]);

  selectedTable = signal('dim_artista');
  searchFilter = signal('');
  page = signal(1);
  pageSize = 8;

  tables: WarehouseTable[] = [
    {
      name: 'dim_usuario', kind: 'dimension', layer: 'gold', rowCount: 1250,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_usuario', type: 'INTEGER' },
        { name: 'nombre_usuario', type: 'VARCHAR' },
        { name: 'pais', type: 'VARCHAR' },
        { name: 'tipo_suscripcion', type: 'VARCHAR' },
      ],
      previewRows: [
        { id_usuario: 1, nombre_usuario: 'user_sp_001', pais: 'ES', tipo_suscripcion: 'premium' },
        { id_usuario: 2, nombre_usuario: 'user_sp_002', pais: 'MX', tipo_suscripcion: 'free' },
        { id_usuario: 3, nombre_usuario: 'user_sp_003', pais: 'CO', tipo_suscripcion: 'premium' },
      ],
    },
    {
      name: 'dim_artista', kind: 'dimension', layer: 'gold', rowCount: 3420,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_artista', type: 'INTEGER' },
        { name: 'nombre_artista', type: 'VARCHAR' },
        { name: 'genero_principal', type: 'VARCHAR' },
        { name: 'popularidad', type: 'INTEGER' },
      ],
      previewRows: [
        { id_artista: 1, nombre_artista: 'The Weeknd', genero_principal: 'R&B', popularidad: 92 },
        { id_artista: 2, nombre_artista: 'Dua Lipa', genero_principal: 'Pop', popularidad: 89 },
        { id_artista: 3, nombre_artista: 'Bad Bunny', genero_principal: 'Reggaetón', popularidad: 90 },
        { id_artista: 4, nombre_artista: 'Billie Eilish', genero_principal: 'Alternative', popularidad: 87 },
      ],
    },
    {
      name: 'dim_genero', kind: 'dimension', layer: 'gold', rowCount: 114,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_genero', type: 'INTEGER' },
        { name: 'nombre_genero', type: 'VARCHAR' },
      ],
      previewRows: [
        { id_genero: 1, nombre_genero: 'Pop' },
        { id_genero: 2, nombre_genero: 'Rock' },
        { id_genero: 3, nombre_genero: 'Hip-Hop' },
      ],
    },
    {
      name: 'dim_album', kind: 'dimension', layer: 'gold', rowCount: 8900,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_album', type: 'INTEGER' },
        { name: 'nombre_album', type: 'VARCHAR' },
        { name: 'id_artista', type: 'INTEGER' },
        { name: 'anio', type: 'INTEGER' },
      ],
      previewRows: [
        { id_album: 101, nombre_album: 'After Hours', id_artista: 1, anio: 2020 },
        { id_album: 102, nombre_album: 'Future Nostalgia', id_artista: 2, anio: 2020 },
      ],
    },
    {
      name: 'dim_track', kind: 'dimension', layer: 'gold', rowCount: 45200,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_track', type: 'INTEGER' },
        { name: 'nombre_track', type: 'VARCHAR' },
        { name: 'id_artista', type: 'INTEGER' },
        { name: 'duracion_ms', type: 'INTEGER' },
      ],
      previewRows: [
        { id_track: 1001, nombre_track: 'Blinding Lights', id_artista: 1, duracion_ms: 200040 },
        { id_track: 1002, nombre_track: 'Levitating', id_artista: 2, duracion_ms: 203064 },
      ],
    },
    {
      name: 'dim_playlist', kind: 'dimension', layer: 'gold', rowCount: 2100,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_playlist', type: 'INTEGER' },
        { name: 'nombre_playlist', type: 'VARCHAR' },
        { name: 'total_tracks', type: 'INTEGER' },
      ],
      previewRows: [
        { id_playlist: 1, nombre_playlist: 'Top Hits Global', total_tracks: 50 },
        { id_playlist: 2, nombre_playlist: 'Discover Weekly', total_tracks: 30 },
      ],
    },
    {
      name: 'dim_tiempo', kind: 'dimension', layer: 'gold', rowCount: 3650,
      lastUpdated: '2026-05-20 14:32',
      columns: [
        { name: 'id_tiempo', type: 'INTEGER' },
        { name: 'fecha', type: 'DATE' },
        { name: 'anio', type: 'INTEGER' },
        { name: 'mes', type: 'INTEGER' },
      ],
      previewRows: [
        { id_tiempo: 20250101, fecha: '2025-01-01', anio: 2025, mes: 1 },
        { id_tiempo: 20250102, fecha: '2025-01-02', anio: 2025, mes: 1 },
      ],
    },
    {
      name: 'fact_streaming', kind: 'fact', layer: 'gold', rowCount: 1280000,
      lastUpdated: '2026-05-20 14:35',
      columns: [
        { name: 'id_stream', type: 'BIGINT' },
        { name: 'id_usuario', type: 'INTEGER' },
        { name: 'id_track', type: 'INTEGER' },
        { name: 'id_tiempo', type: 'INTEGER' },
        { name: 'ms_reproducidos', type: 'INTEGER' },
      ],
      previewRows: [
        { id_stream: 900001, id_usuario: 1, id_track: 1001, id_tiempo: 20250101, ms_reproducidos: 180000 },
        { id_stream: 900002, id_usuario: 2, id_track: 1002, id_tiempo: 20250101, ms_reproducidos: 195000 },
      ],
    },
    {
      name: 'agg_top_artistas', kind: 'aggregation', layer: 'gold', rowCount: 100,
      lastUpdated: '2026-05-20 14:36',
      columns: [
        { name: 'id_artista', type: 'INTEGER' },
        { name: 'nombre_artista', type: 'VARCHAR' },
        { name: 'total_streams', type: 'BIGINT' },
        { name: 'ranking', type: 'INTEGER' },
      ],
      previewRows: [
        { id_artista: 1, nombre_artista: 'The Weeknd', total_streams: 2450000, ranking: 1 },
        { id_artista: 2, nombre_artista: 'Bad Bunny', total_streams: 2100000, ranking: 2 },
      ],
    },
    {
      name: 'agg_genero_popularidad', kind: 'aggregation', layer: 'gold', rowCount: 114,
      lastUpdated: '2026-05-20 14:36',
      columns: [
        { name: 'id_genero', type: 'INTEGER' },
        { name: 'nombre_genero', type: 'VARCHAR' },
        { name: 'popularidad_promedio', type: 'DOUBLE' },
        { name: 'total_tracks', type: 'INTEGER' },
      ],
      previewRows: [
        { id_genero: 1, nombre_genero: 'Pop', popularidad_promedio: 72.4, total_tracks: 8420 },
        { id_genero: 2, nombre_genero: 'Rock', popularidad_promedio: 65.1, total_tracks: 5230 },
      ],
    },
    {
      name: 'agg_distribucion_energia', kind: 'aggregation', layer: 'gold', rowCount: 10,
      lastUpdated: '2026-05-20 14:36',
      columns: [
        { name: 'rango_energia', type: 'VARCHAR' },
        { name: 'cantidad_tracks', type: 'INTEGER' },
        { name: 'popularidad_promedio', type: 'DOUBLE' },
      ],
      previewRows: [
        { rango_energia: '0.0-0.2', cantidad_tracks: 4200, popularidad_promedio: 45.2 },
        { rango_energia: '0.8-1.0', cantidad_tracks: 8900, popularidad_promedio: 78.6 },
      ],
    },
    {
      name: 'agg_tracks_populares', kind: 'aggregation', layer: 'gold', rowCount: 500,
      lastUpdated: '2026-05-20 14:36',
      columns: [
        { name: 'id_track', type: 'INTEGER' },
        { name: 'nombre_track', type: 'VARCHAR' },
        { name: 'popularidad', type: 'INTEGER' },
        { name: 'total_streams', type: 'BIGINT' },
      ],
      previewRows: [
        { id_track: 1001, nombre_track: 'Blinding Lights', popularidad: 89, total_streams: 3200000 },
        { id_track: 1002, nombre_track: 'Levitating', popularidad: 85, total_streams: 2800000 },
      ],
    },
  ];

  filteredTables = computed(() => {
    const q = this.searchFilter().toLowerCase().trim();
    if (!q) return this.tables;
    return this.tables.filter((t) => t.name.toLowerCase().includes(q));
  });

  activeTable = computed(() =>
    this.tables.find((t) => t.name === this.selectedTable()) ?? this.tables[1]
  );

  mockQuery = computed(() => {
    const t = this.activeTable();
    const cols = t.columns.map((c) => c.name).join(', ');
    return `SELECT ${cols}\nFROM ${t.name}\nLIMIT ${this.pageSize}\nOFFSET ${(this.page() - 1) * this.pageSize};`;
  });

  previewColumns = computed(() => this.activeTable().columns.map((c) => c.name));

  totalPages = computed(() =>
    Math.max(1, Math.ceil(this.activeTable().previewRows.length / this.pageSize))
  );

  pagedRows = computed(() => {
    const rows = this.activeTable().previewRows;
    const start = (this.page() - 1) * this.pageSize;
    return rows.slice(start, start + this.pageSize);
  });

  kindCounts = computed(() => ({
    dimension: this.tables.filter((t) => t.kind === 'dimension').length,
    fact: this.tables.filter((t) => t.kind === 'fact').length,
    aggregation: this.tables.filter((t) => t.kind === 'aggregation').length,
  }));

  constructor(private stats: StatsService) {}

  ngOnInit() {
    this.stats.getLastLoads(10).subscribe({
      next: (d) => { this.loads.set(d ?? []); this.isLoadingLoads.set(false); },
      error: () => { this.hasError.set(true); this.isLoadingLoads.set(false); },
    });
  }

  selectTable(name: string) {
    this.selectedTable.set(name);
    this.page.set(1);
  }

  onFilterChange(value: string) {
    this.searchFilter.set(value);
  }

  kindLabel(kind: TableKind): string {
    const map: Record<TableKind, string> = {
      dimension: 'Dimensión', fact: 'Hecho', aggregation: 'Agregación',
    };
    return map[kind];
  }

  kindClass(kind: TableKind): string {
    return `kind-${kind}`;
  }

  fmt(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toLocaleString('es-ES');
  }

  goPage(p: number) {
    if (p < 1 || p > this.totalPages()) return;
    this.page.set(p);
  }

  cellValue(row: Record<string, string | number>, col: string): string {
    const v = row[col];
    return v != null ? String(v) : '—';
  }
}
