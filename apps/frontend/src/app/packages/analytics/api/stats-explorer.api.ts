import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { TablePreview, WarehouseTableMeta } from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class StatsExplorerApi {
  private readonly http = inject(HttpClient);
  private readonly BASE = `${environment.apiUrl}/analytics/explorer`;

  getExplorerTables(): Observable<WarehouseTableMeta[]> {
    return this.http.get<WarehouseTableMeta[]>(`${this.BASE}/tables`);
  }

  getTablePreview(table: string, page = 1, limit = 50): Observable<TablePreview> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http.get<TablePreview>(`${this.BASE}/preview/${table}`, { params });
  }
}
