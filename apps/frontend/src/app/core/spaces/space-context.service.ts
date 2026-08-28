import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
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
  artistSpace,
  dataOpsSpace,
  homePathForSpace,
  organizationSpace,
  personalSpace,
  platformAdminSpace,
} from './space.models';
import {
  SessionBootstrap,
  SessionBootstrapError,
  SessionSpace,
} from './session-bootstrap.model';
import {
  isPersistedSpaceStillValid,
  toPersistedRef,
} from './space-access.policy';
import { SpaceNavSection, spaceNavSectionsFor } from './space-nav.config';
import { isPersonalSurfacePath, normalizeIdentityRole } from '../navigation/nav-access.policy';
import {
  STAFF_CAPABILITY,
  type ProductOrganizationTier,
  type ProductSurfaceContext,
} from '../product-surface';

/** Bootstrap rejected by the backend — the interceptor already dropped the session. */
const UNAUTHORIZED_REASON = 'session_unauthorized';

/**
 * Product space context (045 + 046).
 * Selects Personal / Organization / Artist / Data Ops / Platform Admin.
 * Does NOT change identity role. Does NOT stop the global player.
 * Artist spaces come only from GET /artist-space/mine (real memberships).
 */
@Injectable({ providedIn: 'root' })
export class SpaceContextService {
  private readonly http = inject(HttpClient);
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
  private readonly _manifest = signal<SessionBootstrap | null>(null);
  private artistMembershipCache: ArtistSpaceMineItem[] = [];
  private readonly sessionApi = `${environment.apiUrl}/session`;

  readonly status = this._status.asReadonly();
  readonly availableSpaces = this._available.asReadonly();
  readonly activeSpace = this._active.asReadonly();
  readonly error = this._error.asReadonly();
  /** False once GET /artist-space/mine succeeds (even if empty). */
  readonly artistBackendMissing = this._artistBackendMissing.asReadonly();
  readonly manifest = this._manifest.asReadonly();

  readonly activeSpaceKind = computed(() => this._active()?.kind ?? null);
  readonly hasMultipleSpaces = computed(() => this._available().length > 1);
  readonly showSpaceSelector = computed(
    () => this.auth.isAuthenticated() && this._available().length > 1,
  );

  /** Spec 054 — hydrated facts for the product-surface evaluator (no username / presentation). */
  readonly productSurfaceContext = computed((): ProductSurfaceContext => {
    const space = this._active();
    const kind = space?.kind ?? 'personal';
    const ready = this._status() === 'ready';
    const role = (this.auth.role() || 'user').toLowerCase();
    const staffCapabilities = new Set<string>();
    if (role === 'admin' || role === 'engineer') {
      staffCapabilities.add(STAFF_CAPABILITY.shell);
      staffCapabilities.add(STAFF_CAPABILITY.engineering);
    }
    const tier = this.orgCtx.accessTier();
    const organizationTier: ProductOrganizationTier | undefined =
      tier === 'onboarding' || tier === 'recovery' || tier === 'operational'
        ? tier
        : undefined;
    return {
      ready,
      activeSpace: kind,
      organizationId: space?.organizationId ?? this.orgCtx.organizationId() ?? undefined,
      organizationTier,
      permissions: new Set(this.orgCtx.hasMembership() ? this.orgCtx.permissions() : []),
      artistCapabilities: new Set(this.artistCtx.permissions()),
      staffCapabilities,
      platformRoles: new Set(this.crmCtx.roles()),
    };
  });

  readonly navSections = computed((): SpaceNavSection[] => {
    this.i18n.tick();
    const space = this._active();
    const kind = space?.kind ?? 'personal';
    return spaceNavSectionsFor(kind, {
      organizationId: space?.organizationId ?? null,
      access: this.productSurfaceContext(),
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
    const previous = this._active();
    const target = this._available().find((s) => s.id === spaceId);
    if (!target) {
      return false;
    }
    try {
      const body = await firstValueFrom(
        this.http.post<SessionBootstrap>(`${this.sessionApi}/context`, {
          space_key: toApiSpaceKey(target),
        }),
      );
      this.applyManifest(body);
      await this.applySpace(target, {
        persist: true,
        navigate: options?.navigate !== false,
      });
      return true;
    } catch {
      if (previous) {
        this._active.set(previous);
      }
      return false;
    }
  }

  /**
   * Authoritative session manifest. Throws instead of inventing spaces so callers
   * can surface a retry rather than route the user into a fabricated context.
   */
  async bootstrapFromSession(): Promise<SessionBootstrap> {
    await this.bootstrap({ force: true });
    const manifest = this._manifest();
    if (this._status() !== 'ready' || !manifest) {
      throw new SessionBootstrapError(
        this._error() || 'session_bootstrap_failed',
        this._error() === UNAUTHORIZED_REASON,
      );
    }
    return manifest;
  }

  async completeFirstAccess(intent?: string): Promise<void> {
    try {
      const body = await firstValueFrom(
        this.http.post<SessionBootstrap>(`${this.sessionApi}/first-access`, {
          intent: intent ?? null,
        }),
      );
      this.applyManifest(body);
    } catch {
      /* first-access is advisory */
    }
  }

  /**
   * Align active space with the current URL so staff surfaces never show Personal
   * as the primary context. Does not navigate.
   */
  async ensureSpaceMatchesRoute(url?: string): Promise<void> {
    if (this._status() !== 'ready') return;
    const spaces = this._available();
    const active = this._active();
    if (!active || !spaces.length) return;
    const next = this.preferStaffSpaceForCurrentRoute(
      active,
      spaces,
      (url || this.router.url || '').split('?')[0] || '/',
    );
    if (next.id === active.id) return;
    await this.applySpace(next, { persist: true, navigate: false });
  }

  clear(): void {
    this._available.set([]);
    this._active.set(null);
    this._status.set('idle');
    this._error.set(null);
    this._manifest.set(null);
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
      const remote = await this.fetchSessionBootstrap();
      await Promise.all([
        this.orgCtx.ensureReady().catch(() => undefined),
        this.crmCtx.bootstrap().catch(() => undefined),
        this.fetchArtistMemberships(),
      ]);
      this.applyManifest(remote);
      const spaces = this._available();
      const candidate =
        spaces.find((s) => s.id === appSpaceIdFromKey(remote.active_space_key)) ??
        isPersistedSpaceStillValid(this.readPersisted(), spaces) ??
        spaces.find((s) => s.kind === 'personal') ??
        spaces[0];
      const chosen = candidate
        ? this.preferStaffSpaceForCurrentRoute(
            candidate,
            spaces,
            (this.router.url || '').split('?')[0] || '/',
          )
        : candidate;
      if (!chosen) {
        this.failBootstrap(new Error('session_bootstrap_empty_spaces'));
        return;
      }
      await this.applySpace(chosen, { persist: true, navigate: false });
      this._status.set('ready');
    } catch (e) {
      this.failBootstrap(e);
    }
  }

  /**
   * Bootstrap failure is a hard error: the client never guesses which spaces the
   * account owns, otherwise the UI would authorize surfaces the backend did not grant.
   */
  private failBootstrap(error: unknown): void {
    const unauthorized = error instanceof HttpErrorResponse && error.status === 401;
    this._available.set([]);
    this._active.set(null);
    this._manifest.set(null);
    this.artistMembershipCache = [];
    this.artistCtx.clear();
    this._status.set('error');
    this._error.set(
      unauthorized
        ? UNAUTHORIZED_REASON
        : error instanceof HttpErrorResponse
          ? `session_bootstrap_http_${error.status}`
          : error instanceof Error
            ? error.message
            : 'session_bootstrap_failed',
    );
  }

  /**
   * If the current URL is a staff/technical surface and active space is Personal,
   * switch to Data Ops (engineer) or Organization (admin) when available.
   */
  private preferStaffSpaceForCurrentRoute(
    chosen: AppSpace,
    spaces: AppSpace[],
    path = (this.router.url || '').split('?')[0] || '/',
  ): AppSpace {
    if (isPersonalSurfacePath(path)) {
      return spaces.find((space) => space.kind === 'personal') ?? chosen;
    }

    const organizationMatch = path.match(/^\/organizations\/(\d+)(?:\/|$)/);
    if (organizationMatch) {
      const organizationId = Number(organizationMatch[1]);
      return (
        spaces.find(
          (space) =>
            space.kind === 'organization' && space.organizationId === organizationId,
        ) ?? chosen
      );
    }

    // Enterprise/reporting routes are organization context even when the
    // persisted space still points at Personal (for example after a refresh).
    if (
      path.startsWith('/business') ||
      path.startsWith('/reports') ||
      path.startsWith('/simple-reports') ||
      path.startsWith('/complex-reports') ||
      path.startsWith('/subscriptions') ||
      path.startsWith('/billing') ||
      path.startsWith('/royalties') ||
      path.startsWith('/payouts')
    ) {
      return (
        this.inferFromOrgContext(spaces) ??
        spaces.find((space) => space.kind === 'organization') ??
        chosen
      );
    }

    if (chosen.kind !== 'personal') return chosen;

    const role = normalizeIdentityRole(this.auth.role());
    if (role === 'engineer') {
      return spaces.find((s) => s.kind === 'data_ops') ?? chosen;
    }
    if (role === 'admin') {
      return (
        this.inferFromOrgContext(spaces) ??
        spaces.find((s) => s.kind === 'organization') ??
        spaces.find((s) => s.kind === 'platform_admin') ??
        chosen
      );
    }
    return chosen;
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

  private inferFromOrgContext(spaces: AppSpace[]): AppSpace | null {
    const orgId = this.orgCtx.organizationId();
    if (orgId == null) return null;
    return spaces.find((s) => s.kind === 'organization' && s.organizationId === orgId) ?? null;
  }

  /** Rejects on HTTP failure — callers must not fall back to a locally built manifest. */
  private fetchSessionBootstrap(): Promise<SessionBootstrap> {
    return firstValueFrom(
      this.http.get<SessionBootstrap>(`${this.sessionApi}/bootstrap`),
    );
  }

  private applyManifest(manifest: SessionBootstrap): void {
    this._manifest.set(manifest);
    const t = (key: string) => this.i18n.t(key);
    this._available.set(
      (manifest.spaces || [])
        .filter((space) => space.capabilities.some((capability) => capability.allowed))
        .map((space) => appSpaceFromSession(space, t)),
    );
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

function toApiSpaceKey(space: AppSpace): string {
  if (space.kind === 'organization') return `organization:${space.organizationId}`;
  if (space.kind === 'artist') return `artist:${space.artistProfileId}`;
  return space.kind;
}

function appSpaceIdFromKey(key: string): string {
  if (key.startsWith('organization:')) return `org:${key.split(':')[1]}`;
  return key;
}

function appSpaceFromSession(item: SessionSpace, t: (key: string) => string): AppSpace {
  switch (item.kind) {
    case 'personal':
      return personalSpace(t('spaces.personal') || item.display_name);
    case 'data_ops':
      return dataOpsSpace(t('spaces.dataOps') || item.display_name);
    case 'platform_admin':
      return platformAdminSpace(t('spaces.platformAdmin') || item.display_name);
    case 'organization': {
      const id = Number(item.key.split(':')[1]);
      return organizationSpace(id, item.display_name);
    }
    case 'artist': {
      const id = Number(item.key.split(':')[1]);
      return artistSpace(id, item.display_name);
    }
    default: {
      const _exhaustive: never = item.kind;
      return personalSpace(String(_exhaustive));
    }
  }
}
