import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ArtistAccessRequest,
  ArtistSpaceMineItem,
  ArtistSpaceSummary,
} from '../models/artist-space.models';

const BASE = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class ArtistSpaceApiService {
  private readonly http = inject(HttpClient);

  listMine(): Observable<ArtistSpaceMineItem[]> {
    return this.http.get<ArtistSpaceMineItem[]>(`${BASE}/artist-space/mine`);
  }

  summary(artistProfileId: number): Observable<ArtistSpaceSummary> {
    return this.http.get<ArtistSpaceSummary>(
      `${BASE}/artist-space/${artistProfileId}/summary`,
    );
  }

  profile(artistProfileId: number): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(
      `${BASE}/artist-space/${artistProfileId}/profile`,
    );
  }

  patchProfile(
    artistProfileId: number,
    body: { display_name?: string; legal_name?: string | null },
  ): Observable<Record<string, unknown>> {
    return this.http.patch<Record<string, unknown>>(
      `${BASE}/artist-space/${artistProfileId}/profile`,
      body,
    );
  }

  tracks(artistProfileId: number): Observable<{ items: unknown[]; total: number }> {
    return this.http.get<{ items: unknown[]; total: number }>(
      `${BASE}/artist-space/${artistProfileId}/tracks`,
    );
  }

  releases(artistProfileId: number): Observable<{ items: unknown[]; total: number }> {
    return this.http.get<{ items: unknown[]; total: number }>(
      `${BASE}/artist-space/${artistProfileId}/releases`,
    );
  }

  team(artistProfileId: number): Observable<unknown[]> {
    return this.http.get<unknown[]>(`${BASE}/artist-space/${artistProfileId}/team`);
  }

  invite(
    artistProfileId: number,
    body: { email: string; role: string },
  ): Observable<{
    invite_token: string;
    email_delivery_status: string;
    invitation_id: number;
  }> {
    return this.http.post<{
      invite_token: string;
      email_delivery_status: string;
      invitation_id: number;
    }>(`${BASE}/artist-space/${artistProfileId}/invitations`, body);
  }

  revokeMember(artistProfileId: number, membershipId: number): Observable<unknown> {
    return this.http.post(
      `${BASE}/artist-space/${artistProfileId}/team/${membershipId}/revoke`,
      {},
    );
  }

  changeRole(
    artistProfileId: number,
    membershipId: number,
    role: string,
  ): Observable<unknown> {
    return this.http.patch(
      `${BASE}/artist-space/${artistProfileId}/team/${membershipId}`,
      { role },
    );
  }

  listAccessRequests(artistProfileId: number): Observable<ArtistAccessRequest[]> {
    return this.http.get<ArtistAccessRequest[]>(
      `${BASE}/artist-space/${artistProfileId}/access-requests`,
    );
  }

  approveAccessRequest(artistProfileId: number, reqId: number): Observable<unknown> {
    return this.http.post(
      `${BASE}/artist-space/${artistProfileId}/access-requests/${reqId}/approve`,
      {},
    );
  }

  rejectAccessRequest(
    artistProfileId: number,
    reqId: number,
    reason?: string,
  ): Observable<unknown> {
    return this.http.post(
      `${BASE}/artist-space/${artistProfileId}/access-requests/${reqId}/reject`,
      { reason: reason ?? null },
    );
  }

  createAccessRequest(body: {
    request_type: string;
    warehouse_artist_id?: number | null;
    target_artist_profile_id?: number | null;
    proposed_display_name?: string | null;
    proposed_role?: string | null;
  }): Observable<ArtistAccessRequest> {
    return this.http.post<ArtistAccessRequest>(`${BASE}/artist-access/requests`, body);
  }

  listMyAccessRequests(): Observable<ArtistAccessRequest[]> {
    return this.http.get<ArtistAccessRequest[]>(`${BASE}/artist-access/requests/mine`);
  }

  cancelAccessRequest(id: number): Observable<unknown> {
    return this.http.delete(`${BASE}/artist-access/requests/${id}`);
  }

  acceptInvitation(token: string): Observable<unknown> {
    return this.http.post(`${BASE}/artist-invitations/${encodeURIComponent(token)}/accept`, {});
  }

  listPlatformRequests(status = 'pending'): Observable<ArtistAccessRequest[]> {
    const params = new HttpParams().set('status', status);
    return this.http.get<ArtistAccessRequest[]>(`${BASE}/platform/artist-requests`, {
      params,
    });
  }

  approvePlatformRequest(id: number): Observable<unknown> {
    return this.http.post(`${BASE}/platform/artist-requests/${id}/approve`, {});
  }

  rejectPlatformRequest(id: number, reason?: string): Observable<unknown> {
    return this.http.post(`${BASE}/platform/artist-requests/${id}/reject`, {
      reason: reason ?? null,
    });
  }

  searchCatalogArtists(search: string): Observable<{
    items: Array<{ id_artista: number; nombre_artista: string }>;
    total: number;
  }> {
    const params = new HttpParams().set('search', search).set('limit', '20');
    return this.http.get<{
      items: Array<{ id_artista: number; nombre_artista: string }>;
      total: number;
    }>(`${BASE}/catalog/artists`, { params });
  }
}
