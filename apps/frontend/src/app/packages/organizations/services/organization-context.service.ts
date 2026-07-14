import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import {
  Membership,
  Organization,
} from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from './organizations-api.service';
import { CrmContextService } from '../../crm/services/crm-context.service';
import { I18nService } from '../../../core/services/i18n.service';

export type OrgContextState = 'idle' | 'loading' | 'ready' | 'error';

/**
 * Organization UI state. Authorization always revalidated via API —
 * never treat local signals as the source of truth for permissions.
 */
@Injectable({ providedIn: 'root' })
export class OrganizationContextService {
  private readonly api = inject(OrganizationsApiService);
  private readonly i18n = inject(I18nService);
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

  /** True only when an org is active with a concrete id (not "selected" without context). */
  readonly hasOrganization = computed(
    () => this._active()?.id != null && this._contextKind() === 'active',
  );
  readonly isLoading = computed(() => this._status() === 'loading');

  /** Active org id or null — never invent an id when context is cleared. */
  readonly organizationId = computed(() =>
    this.hasOrganization() ? (this._active()?.id ?? null) : null,
  );

  /** In-flight bootstrap so concurrent callers (route guards) share one load. */
  private bootstrapPromise: Promise<void> | null = null;
  private activatePromise: Promise<void> | null = null;

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

  /**
   * Personal / none mode: clear local org context so the selector cannot
   * show a selected org while organizationId is null.
   * (Backend "current" remains until the next activate; listing still works.)
   */
  enterPersonalMode(): void {
    this.clearOrganizationScopedState();
    this._status.set('ready');
    this._error.set(null);
  }

  /** Wait until org context is ready (or error). Safe to call from parallel route guards. */
  async ensureReady(): Promise<void> {
    if (this.activatePromise) {
      try {
        await this.activatePromise;
      } catch {
        /* activate failure already reflected on signals */
      }
    }
    if (this._status() === 'ready' || this._status() === 'error') return;
    await this.bootstrap();
  }

  async bootstrap(options?: { force?: boolean }): Promise<void> {
    if (this.bootstrapPromise) {
      if (!options?.force) return this.bootstrapPromise;
      await this.bootstrapPromise.catch(() => undefined);
    }

    this.bootstrapPromise = this.runBootstrap().finally(() => {
      this.bootstrapPromise = null;
    });
    return this.bootstrapPromise;
  }

  /** Retry after network/API failure (e.g. open selector again). */
  async retryBootstrap(): Promise<void> {
    return this.bootstrap({ force: true });
  }

  private friendlyError(e: unknown): string {
    if (e instanceof OrganizationsApiError) {
      if (e.code === 'network_error' || e.message === 'network_error' || /failed to fetch/i.test(e.message)) {
        return this.i18n.t('organizations.selector.networkError');
      }
      return e.message || this.i18n.t('organizations.selector.loadError');
    }
    return this.i18n.t('organizations.selector.loadError');
  }

  private async runBootstrap(): Promise<void> {
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
      } else if (
        (current.context === 'none' || current.context === 'invalid') &&
        list.length === 1
      ) {
        // Single visible org: activate so post-login is not "Sin organización".
        try {
          await this.activate(list[0].id);
          return;
        } catch {
          this.clearOrganizationScopedState();
          this._contextKind.set(current.context);
        }
      } else {
        this.clearOrganizationScopedState();
        this._contextKind.set(current.context);
      }
      this._status.set('ready');
    } catch (e) {
      this._status.set('error');
      this._error.set(this.friendlyError(e));
    }
  }

  async refreshList(): Promise<void> {
    const list = await firstValueFrom(this.api.listMine());
    this._organizations.set(list);
  }

  async activate(organizationId: number): Promise<void> {
    if (this.activatePromise) {
      await this.activatePromise;
      if (this._active()?.id === organizationId && this._contextKind() === 'active') {
        return;
      }
    }

    const run = async (): Promise<void> => {
      this._status.set('loading');
      this._error.set(null);
      // Keep previous active org visible until the new context succeeds —
      // avoids selector showing "none" while /organizations/none is wrongfully open.
      try {
        const current = await firstValueFrom(this.api.activate(organizationId));
        await this.refreshList();
        this.crmCtx?.clearState();
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
        this.clearOrganizationScopedState();
        this._status.set('error');
        this._error.set(
          e instanceof OrganizationsApiError &&
            (e.code === 'network_error' || e.message === 'network_error' || /failed to fetch/i.test(e.message))
            ? this.i18n.t('organizations.selector.networkError')
            : e instanceof OrganizationsApiError
              ? e.message
              : this.i18n.t('organizations.selector.loadError'),
        );
        throw e;
      }
    };

    this.activatePromise = run().finally(() => {
      this.activatePromise = null;
    });
    return this.activatePromise;
  }

  async afterCreate(): Promise<void> {
    await this.bootstrap();
  }
}
