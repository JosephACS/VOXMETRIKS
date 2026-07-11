import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/enterprise-api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  readonly baseUrl = environment.apiUrl;
  readonly rootUrl = environment.apiUrl.replace(/\/api\/v\d+\/?$/, '');

  get<T>(
    path: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): Observable<T> {
    return this.getResponse<T>(path, params).pipe(map((res) => this.unwrap(res)));
  }

  getPaginated<T>(
    path: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): Observable<{ items: T; total: number; page: number; pageSize: number }> {
    return this.getResponse<T>(path, params).pipe(
      map((res) => {
        const data = this.unwrap(res);
        const meta = res.meta ?? {};
        return {
          items: data,
          total: meta.total ?? (Array.isArray(data) ? data.length : 0),
          page: meta.page ?? Number(params?.['page'] ?? 1),
          pageSize: meta.page_size ?? meta.limit ?? Number(params?.['page_size'] ?? 20),
        };
      }),
    );
  }

  private getResponse<T>(
    path: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): Observable<ApiResponse<T>> {
    let httpParams = new HttpParams();
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
          httpParams = httpParams.set(key, String(value));
        }
      }
    }
    return this.http
      .get<ApiResponse<T>>(`${this.baseUrl}${path}`, { params: httpParams })
      .pipe(catchError((err) => throwError(() => this.normalizeError(err))));
  }

  getRaw<T>(url: string): Observable<T> {
    return this.http.get<T>(url).pipe(
      catchError((err) => throwError(() => this.normalizeError(err))),
    );
  }

  private unwrap<T>(response: ApiResponse<T>): T {
    if (response.status !== 'success' || response.data === undefined) {
      throw new Error('API returned non-success status');
    }
    return response.data;
  }

  private normalizeError(err: unknown): Error {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return new Error('No se pudo conectar con el servidor. Comprueba que el backend esté en marcha.');
      }
      const detail =
        typeof err.error === 'object' && err.error && 'detail' in err.error
          ? String((err.error as { detail: unknown }).detail)
          : err.message;
      const msg = detail || `HTTP ${err.status}`;
      if (/duckdb|database|warehouse|connection/i.test(msg)) {
        return new Error('Error de conexión con la base de datos analítica (DuckDB).');
      }
      return new Error(msg);
    }
    if (err instanceof Error) return err;
    return new Error('Error desconocido de API');
  }
}
