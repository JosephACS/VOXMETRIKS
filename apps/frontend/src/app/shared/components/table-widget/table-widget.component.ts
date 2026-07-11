import { Component, computed, effect, input, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';

export interface TableColumn<T extends Record<string, unknown>> {
  key: keyof T & string;
  header: string;
  align?: 'left' | 'right';
  format?: 'number' | 'percent' | 'text';
}

@Component({
  selector: 'app-table-widget',
  standalone: true,
  imports: [DecimalPipe, MatTableModule, MatSortModule, MatPaginatorModule],
  templateUrl: './table-widget.component.html',
  styleUrl: './table-widget.component.scss',
})
export class TableWidgetComponent<T extends Record<string, unknown>> {
  readonly title = input<string | null>(null);
  readonly columns = input.required<TableColumn<T>[]>();
  readonly rows = input<T[]>([]);
  readonly pageSize = input(8);

  readonly pageIndex = signal(0);
  readonly sortState = signal<Sort>({ active: '', direction: '' });
  readonly dataSource = new MatTableDataSource<T>();

  readonly displayedColumns = computed(() => this.columns().map((c) => c.key));

  readonly sortedRows = computed(() => {
    const rows = [...this.rows()];
    const sort = this.sortState();
    if (!sort.active || !sort.direction) return rows;
    const dir = sort.direction === 'asc' ? 1 : -1;
    return rows.sort((a, b) => {
      const av = a[sort.active];
      const bv = b[sort.active];
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
      return String(av ?? '').localeCompare(String(bv ?? '')) * dir;
    });
  });

  readonly pagedRows = computed(() => {
    const start = this.pageIndex() * this.pageSize();
    return this.sortedRows().slice(start, start + this.pageSize());
  });

  constructor() {
    effect(() => {
      this.dataSource.data = this.pagedRows();
    });
  }

  onSort(sort: Sort): void {
    this.sortState.set(sort);
    this.pageIndex.set(0);
  }

  onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
  }

  cellValue(row: T, col: TableColumn<T>): string | number | null {
    const v = row[col.key];
    if (v == null) return null;
    if (typeof v === 'string' || typeof v === 'number') return v;
    return String(v);
  }
}
