import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  Membership,
  Organization,
} from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from './organizations-api.service';
import { CrmContextService } from '../../crm/services/crm-context.service';

export type OrgContextState = 'idle' | 'loading' | 'ready' | 'error';

/**
 * Organization UI state. Authorization always revalidated via API —
 * never treat local signals as the source of truth for permissions.
 */
@Injectable({ providedIn: 'root' })
export class OrganizationContextService {
  private readonly api = inject(OrganizationsApiService);
  private readonly crmCtx = inject(CrmContextService, { optional: true });

  private readonly _status = signal<OrgContextState>('idle');
  private readonly _error = signal<string | null>(null);
  private readonly _organizations = signal<Organization[]>([]);
  private readonly _active = signal<Organization | null>(null);
  private readonly _membership = signal<Membership | null>(null);
  private readonly _roles = signal<string[]>([]);
  private readonly _permissions = signal<string[]>([]);
  private readonly _contextKind = signal<'none' | 'active' | 'invalid' | 'access_revoked'>('none');

  readonly status = this._status.asReadonly();
  readonly error = this._error.asReadonly();
  readonly organizations = this._organizations.asReadonly();
  readonly activeOrganization = this._active.asReadonly();
  readonly membership = this._membership.asReadonly();
  readonly roles = this._roles.asReadonly();
  readonly permissions = this._permissions.asReadonly();
  readonly contextKind = this._contextKind.asReadonly();

  readonly hasOrganization = computed(() => this._active() != null && this._contextKind() === 'active');
  readonly isLoading = computed(() => this._status() === 'loading');

  hasPermission(code: string): boolean {
    return this._permissions().includes(code);
  }

  clearOrganizationScopedState(): void {
    this._active.set(null);
    this._membership.set(null);
    this._roles.set([]);
    this._permissions.set([]);
    this._contextKind.set('none');
    this.crmCtx?.clearState();
  }

  async bootstrap(): Promise<void> {
    this._status.set('loading');
    this._error.set(null);
    try {
      const [list, current] = await Promise.all([
        firstValueFrom(this.api.listMine()),
        firstValueFrom(this.api.getCurrent()),
      ]);
      this._organizations.set(list);
      this._contextKind.set(current.context);
      if (current.context === 'active' && current.organization) {
        this._active.set(current.organization);
        this._membership.set(current.membership ?? null);
        this._roles.set(current.roles ?? []);
        this._permissions.set(current.permissions ?? []);
      } else {
        this.clearOrganizationScopedState();
        this._contextKind.set(current.context);
      }
      this._status.set('ready');
    } catch (e) {
      this._status.set('error');
      this._error.set(e instanceof OrganizationsApiError ? e.message : 'Failed to load organizations');
    }
  }

  async refreshList(): Promise<void> {
    const list = await firstValueFrom(this.api.listMine());
    this._organizations.set(list);
  }

  async activate(organizationId: number): Promise<void> {
    this._status.set('loading');
    this._error.set(null);
    try {
      // Clear previous org-scoped permissions/UI before applying new context.
      this.clearOrganizationScopedState();
      const current = await firstValueFrom(this.api.activate(organizationId));
      await this.refreshList();
      this._contextKind.set(current.context);
      if (current.context === 'active' && current.organization) {
        this._active.set(current.organization);
        this._membership.set(current.membership ?? null);
        this._roles.set(current.roles ?? []);
        this._permissions.set(current.permissions ?? []);
      }
      this._status.set('ready');
    } catch (e) {
      this.clearOrganizationScopedState();
      this._status.set('error');
      this._error.set(e instanceof OrganizationsApiError ? e.message : 'Failed to activate organization');
      throw e;
    }
  }

  async afterCreate(): Promise<void> {
    await this.bootstrap();
  }
}
