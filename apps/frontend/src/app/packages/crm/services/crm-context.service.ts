import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from './crm-api.service';

export type CrmContextState = 'idle' | 'loading' | 'ready' | 'error';

/**
 * CRM UI access state. Backend authorizes each request independently —
 * never treat local signals as the source of truth for permissions.
 */
@Injectable({ providedIn: 'root' })
export class CrmContextService {
  private readonly api = inject(CrmApiService);

  private readonly _status = signal<CrmContextState>('idle');
  private readonly _permissions = signal<string[]>([]);
  private readonly _roles = signal<string[]>([]);
  private readonly _error = signal<string | null>(null);

  readonly status = this._status.asReadonly();
  readonly permissions = this._permissions.asReadonly();
  readonly roles = this._roles.asReadonly();
  readonly error = this._error.asReadonly();

  readonly hasCrmAccess = computed(
    () => this._permissions().length > 0 || this._roles().length > 0,
  );
  readonly isLoading = computed(() => this._status() === 'loading');

  hasPermission(code: string): boolean {
    return this._permissions().includes(code);
  }

  clearState(): void {
    this._permissions.set([]);
    this._roles.set([]);
    this._status.set('idle');
    this._error.set(null);
  }

  async bootstrap(): Promise<void> {
    if (this._status() === 'loading') return;
    this._status.set('loading');
    this._error.set(null);
    try {
      const resp = await firstValueFrom(this.api.getPermissions());
      this._permissions.set(resp.permissions ?? []);
      this._roles.set(resp.roles ?? []);
      this._status.set('ready');
    } catch (e) {
      if (e instanceof CrmApiError && e.status === 403) {
        // Authenticated but no CRM roles — treat as no access, not an error
        this._permissions.set([]);
        this._roles.set([]);
        this._status.set('ready');
      } else {
        this._status.set('error');
        this._error.set(
          e instanceof CrmApiError ? e.message : 'No se pudo cargar el contexto CRM',
        );
      }
    }
  }
}
