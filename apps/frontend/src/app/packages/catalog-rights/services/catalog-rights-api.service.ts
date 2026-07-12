import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  AddContractPartyResponse,
  CatalogAsset,
  CatalogAssetArtist,
  CatalogOwnership,
  CatalogRelease,
  PaginatedAssets,
  PaginatedContracts,
  PaginatedReleases,
  RightsApproval,
  RightsAuthorizedUse,
  RightsConflict,
  RightsContract,
  RightsContractParty,
  RightsCoverageRow,
  RightsStatusHistoryEntry,
  RightsTerritory,
  SetTerritoriesResponse,
} from '../models/catalog-rights.models';

const BASE = environment.apiUrl;

/**
 * Catalog Rights & Contracts API client — Spec 021.
 *
 * Mounted at /api/v1/catalog-rights. `app_rights_contract` (this package)
 * is distinct from CRM's `app_commercial_contract` — these are catalog
 * ownership/licensing records, not sales agreements. No legal validity is
 * asserted by this UI; it is a rights-tracking tool only.
 */
@Injectable({ providedIn: 'root' })
export class CatalogRightsApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(orgId) });
  }

  // ── CatalogAsset ─────────────────────────────────────────────────────────

  listAssets(
    orgId: number,
    params?: { status?: string; page?: number; page_size?: number },
  ): Observable<PaginatedAssets> {
    let p = new HttpParams();
    if (params?.status) p = p.set('status', params.status);
    if (params?.page) p = p.set('page', String(params.page));
    if (params?.page_size) p = p.set('page_size', String(params.page_size));
    return this.http.get<PaginatedAssets>(`${BASE}/catalog-rights/assets`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  registerAsset(
    orgId: number,
    body: { title: string; status?: string; warehouse_track_id?: number | null; artist_profile_id?: number | null },
  ): Observable<CatalogAsset> {
    return this.http.post<CatalogAsset>(`${BASE}/catalog-rights/assets`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  getAsset(orgId: number, assetId: number): Observable<CatalogAsset> {
    return this.http.get<CatalogAsset>(`${BASE}/catalog-rights/assets/${assetId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  linkWarehouseTrack(orgId: number, assetId: number, warehouseTrackId: number): Observable<CatalogAsset> {
    return this.http.post<CatalogAsset>(
      `${BASE}/catalog-rights/assets/${assetId}/link-warehouse-track`,
      { warehouse_track_id: warehouseTrackId },
      { headers: this.orgHeaders(orgId) },
    );
  }

  listAssetArtists(orgId: number, assetId: number): Observable<CatalogAssetArtist[]> {
    return this.http.get<CatalogAssetArtist[]>(`${BASE}/catalog-rights/assets/${assetId}/artists`, {
      headers: this.orgHeaders(orgId),
    });
  }

  linkAssetArtist(
    orgId: number,
    assetId: number,
    artistProfileId: number,
    role = 'primary',
  ): Observable<CatalogAssetArtist> {
    return this.http.post<CatalogAssetArtist>(
      `${BASE}/catalog-rights/assets/${assetId}/artists`,
      { artist_profile_id: artistProfileId, role },
      { headers: this.orgHeaders(orgId) },
    );
  }

  listOwnership(orgId: number, assetId: number): Observable<CatalogOwnership[]> {
    return this.http.get<CatalogOwnership[]>(`${BASE}/catalog-rights/assets/${assetId}/ownership`, {
      headers: this.orgHeaders(orgId),
    });
  }

  registerOwnership(
    orgId: number,
    assetId: number,
    body: { ownership_type?: string; owner_organization_id?: number | null; artist_profile_id?: number | null },
  ): Observable<CatalogOwnership> {
    return this.http.post<CatalogOwnership>(
      `${BASE}/catalog-rights/assets/${assetId}/ownership`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  queryCoverage(orgId: number, assetId: number, rightsType?: string): Observable<RightsCoverageRow[]> {
    let p = new HttpParams();
    if (rightsType) p = p.set('rights_type', rightsType);
    return this.http.get<RightsCoverageRow[]>(`${BASE}/catalog-rights/assets/${assetId}/coverage`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  detectOverlap(orgId: number, assetId: number, rightsType: string): Observable<RightsConflict[]> {
    return this.http.post<RightsConflict[]>(
      `${BASE}/catalog-rights/assets/${assetId}/detect-overlap`,
      { rights_type: rightsType },
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── CatalogRelease ───────────────────────────────────────────────────────

  listReleases(orgId: number, params?: { page?: number; page_size?: number }): Observable<PaginatedReleases> {
    let p = new HttpParams();
    if (params?.page) p = p.set('page', String(params.page));
    if (params?.page_size) p = p.set('page_size', String(params.page_size));
    return this.http.get<PaginatedReleases>(`${BASE}/catalog-rights/releases`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  createRelease(
    orgId: number,
    body: { title: string; warehouse_album_id?: number | null },
  ): Observable<CatalogRelease> {
    return this.http.post<CatalogRelease>(`${BASE}/catalog-rights/releases`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── RightsContract ───────────────────────────────────────────────────────

  listContracts(
    orgId: number,
    params?: { asset_id?: number; status?: string; page?: number; page_size?: number },
  ): Observable<PaginatedContracts> {
    let p = new HttpParams();
    if (params?.asset_id) p = p.set('asset_id', String(params.asset_id));
    if (params?.status) p = p.set('status', params.status);
    if (params?.page) p = p.set('page', String(params.page));
    if (params?.page_size) p = p.set('page_size', String(params.page_size));
    return this.http.get<PaginatedContracts>(`${BASE}/catalog-rights/contracts`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  createContract(
    orgId: number,
    body: {
      asset_id: number;
      rights_type: string;
      valid_from: string;
      valid_to?: string | null;
      exclusive?: boolean;
      evidence_ref?: string | null;
    },
  ): Observable<RightsContract> {
    return this.http.post<RightsContract>(`${BASE}/catalog-rights/contracts`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  getContract(orgId: number, contractId: number): Observable<RightsContract> {
    return this.http.get<RightsContract>(`${BASE}/catalog-rights/contracts/${contractId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  archiveContract(orgId: number, contractId: number, reason?: string): Observable<RightsContract> {
    return this.http.post<RightsContract>(
      `${BASE}/catalog-rights/contracts/${contractId}/archive`,
      { reason: reason ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  getContractHistory(orgId: number, contractId: number): Observable<RightsStatusHistoryEntry[]> {
    return this.http.get<RightsStatusHistoryEntry[]>(
      `${BASE}/catalog-rights/contracts/${contractId}/history`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── RightsContractParty ──────────────────────────────────────────────────

  listContractParties(orgId: number, contractId: number): Observable<RightsContractParty[]> {
    return this.http.get<RightsContractParty[]>(
      `${BASE}/catalog-rights/contracts/${contractId}/parties`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  addContractParty(
    orgId: number,
    contractId: number,
    body: {
      party_name: string;
      party_type?: string;
      ownership_percentage: number;
      party_organization_id?: number | null;
      artist_profile_id?: number | null;
    },
  ): Observable<AddContractPartyResponse> {
    return this.http.post<AddContractPartyResponse>(
      `${BASE}/catalog-rights/contracts/${contractId}/parties`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── RightsTerritory ───────────────────────────────────────────────────────

  listContractTerritories(orgId: number, contractId: number): Observable<RightsTerritory[]> {
    return this.http.get<RightsTerritory[]>(
      `${BASE}/catalog-rights/contracts/${contractId}/territories`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  setTerritories(
    orgId: number,
    contractId: number,
    territories: { territory_code: string; territory_name: string }[],
  ): Observable<SetTerritoriesResponse> {
    return this.http.post<SetTerritoriesResponse>(
      `${BASE}/catalog-rights/contracts/${contractId}/territories`,
      { territories },
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── RightsAuthorizedUse ───────────────────────────────────────────────────

  listAuthorizedUses(orgId: number, contractId: number): Observable<RightsAuthorizedUse[]> {
    return this.http.get<RightsAuthorizedUse[]>(
      `${BASE}/catalog-rights/contracts/${contractId}/authorized-uses`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  setAuthorizedUses(
    orgId: number,
    contractId: number,
    uses: { use_code: string; description?: string | null }[],
  ): Observable<RightsAuthorizedUse[]> {
    return this.http.post<RightsAuthorizedUse[]>(
      `${BASE}/catalog-rights/contracts/${contractId}/authorized-uses`,
      { uses },
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── RightsApproval ────────────────────────────────────────────────────────

  submitForApproval(orgId: number, contractId: number): Observable<RightsApproval> {
    return this.http.post<RightsApproval>(
      `${BASE}/catalog-rights/contracts/${contractId}/submit-for-approval`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  approveContract(
    orgId: number,
    contractId: number,
    approved: boolean,
    notes?: string,
  ): Observable<RightsApproval> {
    return this.http.post<RightsApproval>(
      `${BASE}/catalog-rights/contracts/${contractId}/approve`,
      { approved, notes: notes ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  listApprovals(orgId: number, contractId: number): Observable<RightsApproval[]> {
    return this.http.get<RightsApproval[]>(
      `${BASE}/catalog-rights/contracts/${contractId}/approvals`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── RightsConflict ────────────────────────────────────────────────────────

  listConflicts(
    orgId: number,
    params?: { asset_id?: number; status?: string },
  ): Observable<RightsConflict[]> {
    let p = new HttpParams();
    if (params?.asset_id) p = p.set('asset_id', String(params.asset_id));
    if (params?.status) p = p.set('status', params.status);
    return this.http.get<RightsConflict[]>(`${BASE}/catalog-rights/conflicts`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  openConflict(
    orgId: number,
    body: { asset_id: number; rights_type: string; territory_code: string; details?: string | null },
  ): Observable<RightsConflict> {
    return this.http.post<RightsConflict>(`${BASE}/catalog-rights/conflicts`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  resolveConflict(
    orgId: number,
    conflictId: number,
    resolution: string,
    notes?: string,
  ): Observable<RightsConflict> {
    return this.http.post<RightsConflict>(
      `${BASE}/catalog-rights/conflicts/${conflictId}/resolve`,
      { resolution, notes: notes ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }
}
