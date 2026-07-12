import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ArtistAssignment,
  ArtistExternalIdentifier,
  ArtistOrganizationLink,
  ArtistProfile,
  ArtistStatusHistoryEntry,
  ArtistTeamMember,
  PaginatedArtists,
} from '../models/artist.models';

const BASE = environment.apiUrl;

/**
 * Business artist-profile / team-management API client.
 *
 * NOTE: mounted under /artists (not /artists) — the /artists path is
 * already used by the analytics/streaming music-catalog feature backed by
 * dim_artista. See backend router.py docstring / accepted-debt.md.
 */
@Injectable({ providedIn: 'root' })
export class ArtistsApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(orgId) });
  }

  // ── ArtistProfile ────────────────────────────────────────────────────────

  list(
    orgId: number,
    params?: { status?: string; page?: number; page_size?: number },
  ): Observable<PaginatedArtists> {
    let p = new HttpParams();
    if (params?.status) p = p.set('status', params.status);
    if (params?.page) p = p.set('page', String(params.page));
    if (params?.page_size) p = p.set('page_size', String(params.page_size));
    return this.http.get<PaginatedArtists>(`${BASE}/artists`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  create(
    orgId: number,
    body: { display_name: string; legal_name?: string | null; warehouse_artist_id?: number | null },
  ): Observable<ArtistProfile> {
    return this.http.post<ArtistProfile>(`${BASE}/artists`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  get(orgId: number, artistId: number): Observable<ArtistProfile> {
    return this.http.get<ArtistProfile>(`${BASE}/artists/${artistId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  activate(orgId: number, artistId: number, reason?: string): Observable<ArtistProfile> {
    return this.http.post<ArtistProfile>(
      `${BASE}/artists/${artistId}/activate`,
      { reason: reason ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  deactivate(orgId: number, artistId: number, reason?: string): Observable<ArtistProfile> {
    return this.http.post<ArtistProfile>(
      `${BASE}/artists/${artistId}/deactivate`,
      { reason: reason ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  archive(orgId: number, artistId: number, reason?: string): Observable<ArtistProfile> {
    return this.http.post<ArtistProfile>(
      `${BASE}/artists/${artistId}/archive`,
      { reason: reason ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  linkWarehouseArtist(
    orgId: number,
    artistId: number,
    warehouseArtistId: number,
  ): Observable<ArtistProfile> {
    return this.http.post<ArtistProfile>(
      `${BASE}/artists/${artistId}/link-warehouse`,
      { warehouse_artist_id: warehouseArtistId },
      { headers: this.orgHeaders(orgId) },
    );
  }

  transferOrganization(
    orgId: number,
    artistId: number,
    targetOrganizationId: number,
    reason?: string,
  ): Observable<ArtistProfile> {
    return this.http.post<ArtistProfile>(
      `${BASE}/artists/${artistId}/transfer`,
      { target_organization_id: targetOrganizationId, reason: reason ?? null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  getHistory(orgId: number, artistId: number): Observable<ArtistStatusHistoryEntry[]> {
    return this.http.get<ArtistStatusHistoryEntry[]>(
      `${BASE}/artists/${artistId}/history`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── ArtistOrganization ──────────────────────────────────────────────────

  listOrganizations(orgId: number, artistId: number): Observable<ArtistOrganizationLink[]> {
    return this.http.get<ArtistOrganizationLink[]>(
      `${BASE}/artists/${artistId}/organizations`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  linkOrganization(
    orgId: number,
    artistId: number,
    targetOrganizationId: number,
    relationshipRole = 'secondary',
  ): Observable<ArtistOrganizationLink> {
    return this.http.post<ArtistOrganizationLink>(
      `${BASE}/artists/${artistId}/organizations`,
      { target_organization_id: targetOrganizationId, relationship_role: relationshipRole },
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── ArtistAssignment (manager) ──────────────────────────────────────────

  listAssignments(orgId: number, artistId: number): Observable<ArtistAssignment[]> {
    return this.http.get<ArtistAssignment[]>(
      `${BASE}/artists/${artistId}/assignments`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  assignManager(
    orgId: number,
    artistId: number,
    userId: number,
    role = 'manager',
  ): Observable<ArtistAssignment> {
    return this.http.post<ArtistAssignment>(
      `${BASE}/artists/${artistId}/assignments`,
      { user_id: userId, role },
      { headers: this.orgHeaders(orgId) },
    );
  }

  endAssignment(
    orgId: number,
    artistId: number,
    assignmentId: number,
  ): Observable<ArtistAssignment> {
    return this.http.post<ArtistAssignment>(
      `${BASE}/artists/${artistId}/assignments/${assignmentId}/end`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── ArtistTeamMember ─────────────────────────────────────────────────────

  listTeam(orgId: number, artistId: number): Observable<ArtistTeamMember[]> {
    return this.http.get<ArtistTeamMember[]>(`${BASE}/artists/${artistId}/team`, {
      headers: this.orgHeaders(orgId),
    });
  }

  addTeamMember(
    orgId: number,
    artistId: number,
    userId: number,
    teamRole: string,
  ): Observable<ArtistTeamMember> {
    return this.http.post<ArtistTeamMember>(
      `${BASE}/artists/${artistId}/team`,
      { user_id: userId, team_role: teamRole },
      { headers: this.orgHeaders(orgId) },
    );
  }

  removeTeamMember(
    orgId: number,
    artistId: number,
    memberId: number,
  ): Observable<ArtistTeamMember> {
    return this.http.post<ArtistTeamMember>(
      `${BASE}/artists/${artistId}/team/${memberId}/remove`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── ArtistExternalIdentifier ─────────────────────────────────────────────

  listExternalIdentifiers(
    orgId: number,
    artistId: number,
  ): Observable<ArtistExternalIdentifier[]> {
    return this.http.get<ArtistExternalIdentifier[]>(
      `${BASE}/artists/${artistId}/external-identifiers`,
      { headers: this.orgHeaders(orgId) },
    );
  }

  setExternalIdentifier(
    orgId: number,
    artistId: number,
    systemCode: string,
    externalValue: string,
  ): Observable<ArtistExternalIdentifier> {
    return this.http.post<ArtistExternalIdentifier>(
      `${BASE}/artists/${artistId}/external-identifiers`,
      { system_code: systemCode, external_value: externalValue },
      { headers: this.orgHeaders(orgId) },
    );
  }
}
