import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { I18nService } from '../services/i18n.service';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { ArtistContextService } from '../../packages/artist-space/services/artist-context.service';
import { ArtistSpaceApiService } from '../../packages/artist-space/services/artist-space-api.service';
import { ArtistSpaceMineItem } from '../../packages/artist-space/models/artist-space.models';
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
import { SpaceNavSection, spaceNavSectionsFor, filterSpaceNavSections } from './space-nav.config';

/**
 * Product space context (045 + 046).
 * Selects Personal / Organization / Artist / Data Ops / Platform Admin.
 * Does NOT change identity role. Does NOT stop the global player.
 * Artist spaces come only from GET /artist-space/mine (real memberships).
 */
@Injectable({ providedIn: 'root' })
export class SpaceContextService {
  private readonly auth = inject(AuthService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly crmCtx = inject(CrmContextService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly artistApi = inject(ArtistSpaceApiService);
  private readonly i18n = inject(I18nService);
  private readonly router = inject(Router);

  private readonly _status = signal<'idle' | 'loading' | 'ready' | 'error'>('idle');
  private readonly _available = signal<AppSpace[]>([]);
  private readonly _active = signal<AppSpace | null>(null);
  private readonly _error = signal<string | null>(null);
  private readonly _artistBackendMissing = signal(true);
  private artistMembershipCache: ArtistSpaceMineItem[] = [];

  readonly status = this._status.asReadonly();
  readonly availableSpaces = this._available.asReadonly();
  readonly activeSpace = this._active.asReadonly();
  readonly error = this._error.asReadonly();
  /** False once GET /artist-space/mine succeeds (even if empty). */
  readonly artistBackendMissing = this._artistBackendMissing.asReadonly();

  readonly activeSpaceKind = computed(() => this._active()?.kind ?? null);
  readonly hasMultipleSpaces = computed(() => this._available().length > 1);
  readonly showSpaceSelector = computed(
    () => this.auth.isAuthenticated() && this._available().length > 1,
  );

  readonly navSections = computed((): SpaceNavSection[] => {
    this.i18n.tick();
    const space = this._active();
    const kind = space?.kind ?? 'personal';
    const raw = spaceNavSectionsFor(kind, {
      organizationId: space?.organizationId ?? null,
    });
    const role = this.auth.role();
    const hasStaffAccess =
      role === 'admin' ||
      role === 'engineer' ||
      this.crmCtx.roles().includes('platform_admin');
    return filterSpaceNavSections(raw, {
      hasStaffAccess,
      canAccessOrgModule: (moduleKind, requiredPermission) =>
        this.orgCtx.canAccessModule(moduleKind, requiredPermission ?? null),
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

  async selectSpace(spaceId: string, options?: { navigate?: boolean }): Promise<boolean> {
    const target = this._available().find((s) => s.id === spaceId);
    if (!target) {
      return false;
    }
    await this.applySpace(target, { persist: true, navigate: options?.navigate !== false });
    return true;
  }

  clear(): void {
    this._available.set([]);
    this._active.set(null);
    this._status.set('idle');
    this._error.set(null);
    this.artistMembershipCache = [];
    this.artistCtx.clear();
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
        this.fetchArtistMemberships(),
      ]);

      const spaces = this.rebuildAvailable();
      this._available.set(spaces);

      const restored = isPersistedSpaceStillValid(this.readPersisted(), spaces);
      let chosen: AppSpace =
        restored ??
        this.inferFromOrgContext(spaces) ??
        spaces.find((s) => s.kind === 'personal') ??
        personalSpace(this.i18n.t('spaces.personal'));

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
      this.artistCtx.clear();
    }
  }

  private async fetchArtistMemberships(): Promise<void> {
    try {
      const items = await firstValueFrom(this.artistApi.listMine());
      this.artistMembershipCache = Array.isArray(items) ? items : [];
      this._artistBackendMissing.set(false);
    } catch {
      this.artistMembershipCache = [];
      this._artistBackendMissing.set(true);
    }
  }

  private rebuildAvailable(): AppSpace[] {
    const role = this.auth.role();
    const crmRoles = this.crmCtx.roles();
    const hasPlatformAdminSpace =
      role === 'admin' || crmRoles.includes('platform_admin');

    const artistMemberships = this.artistMembershipCache.map((m) => ({
      id: m.artist_profile_id,
      name: m.display_name,
    }));

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
    if (space.kind === 'organization' && space.organizationId != null) {
      if (this.orgCtx.organizationId() !== space.organizationId) {
        await this.orgCtx.activate(space.organizationId);
      }
      this.artistCtx.clear();
    } else if (
      space.kind === 'personal' ||
      space.kind === 'data_ops' ||
      space.kind === 'platform_admin'
    ) {
      if (this.orgCtx.hasOrganization()) {
        this.orgCtx.enterPersonalMode();
      }
      this.artistCtx.clear();
    } else if (space.kind === 'artist' && space.artistProfileId != null) {
      // Never activate OrganizationContext for independent artists (org_id=0).
      if (this.orgCtx.hasOrganization()) {
        this.orgCtx.enterPersonalMode();
      }
      const membership = this.artistMembershipCache.find(
        (m) => m.artist_profile_id === space.artistProfileId,
      );
      if (membership) {
        this.artistCtx.activate(membership);
      } else {
        this.artistCtx.clear();
      }
    }

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
