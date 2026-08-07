import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { I18nService } from '../services/i18n.service';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import {
  AppSpace,
  PersistedSpaceRef,
  SPACE_STORAGE_KEY,
  homePathForSpace,
  personalSpace,
} from './space.models';
import {
  buildAvailableSpaces,
  isPersistedSpaceStillValid,
  toPersistedRef,
} from './space-access.policy';
import { SpaceNavSection, spaceNavSectionsFor } from './space-nav.config';

/**
 * Product space context (045).
 * Selects Personal / Organization / Data Ops / Platform Admin.
 * Does NOT change identity role. Does NOT stop the global player.
 * Artist spaces are architected but empty until a real membership API exists.
 */
@Injectable({ providedIn: 'root' })
export class SpaceContextService {
  private readonly auth = inject(AuthService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly crmCtx = inject(CrmContextService);
  private readonly i18n = inject(I18nService);
  private readonly router = inject(Router);

  private readonly _status = signal<'idle' | 'loading' | 'ready' | 'error'>('idle');
  private readonly _available = signal<AppSpace[]>([]);
  private readonly _active = signal<AppSpace | null>(null);
  private readonly _error = signal<string | null>(null);
  private readonly _artistBackendMissing = signal(true);

  readonly status = this._status.asReadonly();
  readonly availableSpaces = this._available.asReadonly();
  readonly activeSpace = this._active.asReadonly();
  readonly error = this._error.asReadonly();
  /** True until GET artists/mine (or equivalent) exists. */
  readonly artistBackendMissing = this._artistBackendMissing.asReadonly();

  readonly activeSpaceKind = computed(() => this._active()?.kind ?? null);
  readonly hasMultipleSpaces = computed(() => this._available().length > 1);
  /** Selector is prominent only when more than one space is available. */
  readonly showSpaceSelector = computed(
    () => this.auth.isAuthenticated() && this._available().length > 1,
  );

  readonly navSections = computed((): SpaceNavSection[] => {
    const space = this._active();
    if (!space) return spaceNavSectionsFor('personal');
    return spaceNavSectionsFor(space.kind, {
      organizationId: space.organizationId ?? null,
    });
  });

  private readyPromise: Promise<void> | null = null;

  async ensureReady(): Promise<void> {
    if (this._status() === 'ready' || this._status() === 'error') return;
    await this.bootstrap();
  }

  async bootstrap(options?: { force?: boolean }): Promise<void> {
    if (this.readyPromise && !options?.force) return this.readyPromise;
    this.readyPromise = this.runBootstrap().finally(() => {
      this.readyPromise = null;
    });
    return this.readyPromise;
  }

  /**
   * Switch space. Never stops playback. Never changes identity role.
   * @param navigate when true, go to space home (default true on user action)
   */
  async selectSpace(spaceId: string, options?: { navigate?: boolean }): Promise<boolean> {
    const target = this._available().find((s) => s.id === spaceId);
    if (!target) {
      return false;
    }
    await this.applySpace(target, { persist: true, navigate: options?.navigate !== false });
    return true;
  }

  /** Clear on logout. */
  clear(): void {
    this._available.set([]);
    this._active.set(null);
    this._status.set('idle');
    this._error.set(null);
    try {
      localStorage.removeItem(SPACE_STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }

  private async runBootstrap(): Promise<void> {
    if (!this.auth.isAuthenticated()) {
      this.clear();
      return;
    }
    this._status.set('loading');
    this._error.set(null);
    try {
      await Promise.all([
        this.orgCtx.ensureReady(),
        this.crmCtx.bootstrap().catch(() => undefined),
      ]);

      const spaces = this.rebuildAvailable();
      this._available.set(spaces);

      const restored = isPersistedSpaceStillValid(this.readPersisted(), spaces);
      let chosen: AppSpace =
        restored ??
        this.inferFromOrgContext(spaces) ??
        spaces.find((s) => s.kind === 'personal') ??
        personalSpace(this.i18n.t('spaces.personal'));

      // Re-validate after rebuild
      if (!spaces.some((s) => s.id === chosen.id)) {
        chosen = spaces[0] ?? personalSpace(this.i18n.t('spaces.personal'));
      }

      await this.applySpace(chosen, { persist: true, navigate: false });
      this._status.set('ready');
    } catch (e) {
      this._status.set('error');
      this._error.set(e instanceof Error ? e.message : 'space_bootstrap_failed');
      const fallback = personalSpace(this.i18n.t('spaces.personal'));
      this._available.set([fallback]);
      this._active.set(fallback);
    }
  }

  private rebuildAvailable(): AppSpace[] {
    const role = this.auth.role();
    const crmRoles = this.crmCtx.roles();
    const hasPlatformAdminSpace =
      role === 'admin' || crmRoles.includes('platform_admin');

    // Artist memberships: no user-scoped API yet — never invent.
    const artistMemberships: { id: number; name: string }[] = [];
    this._artistBackendMissing.set(true);

    return buildAvailableSpaces({
      authenticated: this.auth.isAuthenticated(),
      identityRole: role,
      hasEngineerAccess: this.auth.hasEngineerAccess(),
      hasPlatformAdminSpace,
      organizations: this.orgCtx.organizations().map((o) => ({
        id: o.id,
        name: o.display_name || o.legal_name || `Organización ${o.id}`,
      })),
      artistMemberships,
      personalLabel: this.i18n.t('spaces.personal'),
      dataOpsLabel: this.i18n.t('spaces.dataOps'),
      platformAdminLabel: this.i18n.t('spaces.platformAdmin'),
    });
  }

  private inferFromOrgContext(spaces: AppSpace[]): AppSpace | null {
    const orgId = this.orgCtx.organizationId();
    if (orgId == null) return null;
    return spaces.find((s) => s.kind === 'organization' && s.organizationId === orgId) ?? null;
  }

  private async applySpace(
    space: AppSpace,
    opts: { persist: boolean; navigate: boolean },
  ): Promise<void> {
    // Data context: org activate vs personal clear. Never touch player.
    if (space.kind === 'organization' && space.organizationId != null) {
      if (this.orgCtx.organizationId() !== space.organizationId) {
        await this.orgCtx.activate(space.organizationId);
      }
    } else if (
      space.kind === 'personal' ||
      space.kind === 'data_ops' ||
      space.kind === 'platform_admin'
    ) {
      if (this.orgCtx.hasOrganization()) {
        this.orgCtx.enterPersonalMode();
      }
    }
    // artist: when implemented, would set org context if required by APIs

    this._active.set(space);
    if (opts.persist) {
      this.writePersisted(toPersistedRef(space));
    }
    if (opts.navigate) {
      const home = homePathForSpace(space);
      await this.router.navigateByUrl(home);
    }
  }

  private readPersisted(): PersistedSpaceRef | null {
    try {
      const raw = localStorage.getItem(SPACE_STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as PersistedSpaceRef;
      if (!parsed?.id || !parsed?.kind) return null;
      return parsed;
    } catch {
      return null;
    }
  }

  private writePersisted(ref: PersistedSpaceRef): void {
    try {
      localStorage.setItem(SPACE_STORAGE_KEY, JSON.stringify(ref));
    } catch {
      /* ignore quota */
    }
  }
}
