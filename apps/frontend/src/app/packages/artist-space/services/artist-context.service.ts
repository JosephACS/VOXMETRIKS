import { Injectable, computed, signal } from '@angular/core';
import {
  ArtistMembershipRole,
  ArtistSpaceMineItem,
  ArtistSpacePermission,
  canAccessArtistPermission,
} from '../models/artist-space.models';

/**
 * Active Artist Space context (046).
 * Does NOT change identity role. Does NOT stop player.
 * Does NOT require / activate OrganizationContext (esp. never org_id=0).
 */
@Injectable({ providedIn: 'root' })
export class ArtistContextService {
  private readonly _artistProfileId = signal<number | null>(null);
  private readonly _membershipRole = signal<ArtistMembershipRole | null>(null);
  private readonly _permissions = signal<string[]>([]);
  private readonly _displayName = signal<string | null>(null);
  private readonly _organizationId = signal<number | null>(null);
  private readonly _warehouseArtistId = signal<number | null>(null);

  readonly artistProfileId = this._artistProfileId.asReadonly();
  readonly membershipRole = this._membershipRole.asReadonly();
  readonly permissions = this._permissions.asReadonly();
  readonly displayName = this._displayName.asReadonly();
  readonly organizationId = this._organizationId.asReadonly();
  readonly warehouseArtistId = this._warehouseArtistId.asReadonly();

  readonly hasArtist = computed(() => this._artistProfileId() != null);

  activate(item: ArtistSpaceMineItem): void {
    this._artistProfileId.set(item.artist_profile_id);
    this._membershipRole.set(item.membership_role);
    this._permissions.set([...(item.permissions ?? [])]);
    this._displayName.set(item.display_name);
    // Independent artists use organization_id=0 — never treat as org context.
    this._organizationId.set(
      item.organization_id && item.organization_id > 0 ? item.organization_id : 0,
    );
    this._warehouseArtistId.set(item.warehouse_artist_id);
  }

  clear(): void {
    this._artistProfileId.set(null);
    this._membershipRole.set(null);
    this._permissions.set([]);
    this._displayName.set(null);
    this._organizationId.set(null);
    this._warehouseArtistId.set(null);
  }

  can(permission: ArtistSpacePermission | string): boolean {
    return canAccessArtistPermission(this._permissions(), permission);
  }
}
