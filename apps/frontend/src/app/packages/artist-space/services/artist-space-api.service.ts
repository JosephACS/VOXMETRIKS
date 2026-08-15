import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ArtistAccessRequest,
  ArtistAccessRequestCreateBody,
  ArtistDiscoveryResponse,
  ArtistInvitation,
  ArtistProfileDetail,
  ArtistProfilePatchBody,
  ArtistSpaceMineItem,
  ArtistSpaceSummary,
  ArtistTeamMember,
} from '../models/artist-space.models';
import {
  ContributorCreateBody,
  MetadataUpdateBody,
  ReleaseDetail,
  ReleaseSubmission,
  StatusHistoryEntry,
  TrackCreateBody,
  ValidateReadyResult,
} from '../../catalog-publishing/models/catalog-publishing.models';

const BASE = environment.apiUrl;

/** Draft body for artist-scoped publishing: the server owns organization AND artist. */
export interface ArtistDraftCreateBody {
  title: string;
  release_type?: string;
  version?: string | null;
  label_name?: string | null;
  genre?: string | null;
  language?: string | null;
  explicit?: boolean;
  planned_release_date?: string | null;
  upc?: string | null;
  rights_contract_id?: number | null;
  idempotency_key?: string | null;
}

/**
 * Artist Space API client (046 + 051).
 *
 * Authorization is the session user plus artist membership; `X-Organization-Id`
 * is never sent — the backend resolves the hidden workspace from the profile.
 */
@Injectable({ providedIn: 'root' })
export class ArtistSpaceApiService {
  private readonly http = inject(HttpClient);

  private publishingBase(artistProfileId: number): string {
    return `${BASE}/artist-space/${artistProfileId}/publishing`;
  }

  listMine(): Observable<ArtistSpaceMineItem[]> {
    return this.http.get<ArtistSpaceMineItem[]>(`${BASE}/artist-space/mine`);
  }

  summary(artistProfileId: number): Observable<ArtistSpaceSummary> {
    return this.http.get<ArtistSpaceSummary>(
      `${BASE}/artist-space/${artistProfileId}/summary`,
    );
  }

  profile(artistProfileId: number): Observable<ArtistProfileDetail> {
    return this.http.get<ArtistProfileDetail>(
      `${BASE}/artist-space/${artistProfileId}/profile`,
    );
  }

  patchProfile(
    artistProfileId: number,
    body: ArtistProfilePatchBody,
  ): Observable<ArtistProfileDetail> {
    return this.http.patch<ArtistProfileDetail>(
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

  team(artistProfileId: number): Observable<ArtistTeamMember[]> {
    return this.http.get<ArtistTeamMember[]>(
      `${BASE}/artist-space/${artistProfileId}/team`,
    );
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

  listInvitations(
    artistProfileId: number,
    status?: string,
  ): Observable<ArtistInvitation[]> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }
    return this.http.get<ArtistInvitation[]>(
      `${BASE}/artist-space/${artistProfileId}/invitations`,
      { params },
    );
  }

  revokeInvitation(artistProfileId: number, invitationId: number): Observable<ArtistInvitation> {
    return this.http.post<ArtistInvitation>(
      `${BASE}/artist-space/${artistProfileId}/invitations/${invitationId}/revoke`,
      {},
    );
  }

  resendInvitation(
    artistProfileId: number,
    invitationId: number,
  ): Observable<{
    invite_token: string;
    email_delivery_status: string;
    invitation_id: number;
  }> {
    return this.http.post<{
      invite_token: string;
      email_delivery_status: string;
      invitation_id: number;
    }>(`${BASE}/artist-space/${artistProfileId}/invitations/${invitationId}/resend`, {});
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

  createAccessRequest(
    body: ArtistAccessRequestCreateBody,
  ): Observable<ArtistAccessRequest> {
    return this.http.post<ArtistAccessRequest>(`${BASE}/artist-access/requests`, body);
  }

  listMyAccessRequests(): Observable<ArtistAccessRequest[]> {
    return this.http.get<ArtistAccessRequest[]>(`${BASE}/artist-access/requests/mine`);
  }

  cancelAccessRequest(id: number): Observable<unknown> {
    return this.http.delete(`${BASE}/artist-access/requests/${id}`);
  }

  /** Accept invitation — token only in JSON body, never in URL path. */
  acceptInvitation(token: string): Observable<unknown> {
    return this.http.post(`${BASE}/artist-invitations/accept`, { token });
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

  /**
   * Discovery is the only entry point for claim/access decisions: the server
   * returns the single allowed action, so the client never offers both CTAs.
   */
  discoverArtists(search: string, limit = 20): Observable<ArtistDiscoveryResponse> {
    const params = new HttpParams().set('search', search).set('limit', String(limit));
    return this.http.get<ArtistDiscoveryResponse>(`${BASE}/artist-access/discover`, {
      params,
    });
  }

  // ── Artist-scoped publishing (051) ────────────────────────────────────────

  listArtistReleases(
    artistProfileId: number,
    params?: { limit?: number; offset?: number },
  ): Observable<ReleaseSubmission[]> {
    let p = new HttpParams();
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    if (params?.offset != null) p = p.set('offset', String(params.offset));
    return this.http.get<ReleaseSubmission[]>(
      `${this.publishingBase(artistProfileId)}/releases`,
      { params: p },
    );
  }

  createArtistRelease(
    artistProfileId: number,
    body: ArtistDraftCreateBody,
  ): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(
      `${this.publishingBase(artistProfileId)}/releases`,
      body,
    );
  }

  getArtistRelease(
    artistProfileId: number,
    submissionId: number,
  ): Observable<ReleaseDetail> {
    return this.http.get<ReleaseDetail>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}`,
    );
  }

  updateArtistRelease(
    artistProfileId: number,
    submissionId: number,
    body: MetadataUpdateBody,
  ): Observable<ReleaseSubmission> {
    return this.http.patch<ReleaseSubmission>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}`,
      body,
    );
  }

  addArtistTrack(
    artistProfileId: number,
    submissionId: number,
    body: TrackCreateBody,
  ): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/tracks`,
      body,
    );
  }

  updateArtistTrack(
    artistProfileId: number,
    submissionId: number,
    trackId: number,
    body: Partial<TrackCreateBody>,
  ): Observable<Record<string, unknown>> {
    return this.http.patch<Record<string, unknown>>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/tracks/${trackId}`,
      body,
    );
  }

  uploadArtistTrackAudio(
    artistProfileId: number,
    submissionId: number,
    trackId: number,
    file: File,
  ): Observable<Record<string, unknown>> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<Record<string, unknown>>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/tracks/${trackId}/audio`,
      fd,
    );
  }

  uploadArtistCover(
    artistProfileId: number,
    submissionId: number,
    file: File,
  ): Observable<Record<string, unknown>> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<Record<string, unknown>>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/cover`,
      fd,
    );
  }

  addArtistContributor(
    artistProfileId: number,
    submissionId: number,
    body: ContributorCreateBody,
  ): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/contributors`,
      body,
    );
  }

  validateArtistRelease(
    artistProfileId: number,
    submissionId: number,
  ): Observable<ValidateReadyResult> {
    return this.http.post<ValidateReadyResult>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/validate`,
      {},
    );
  }

  submitArtistRelease(
    artistProfileId: number,
    submissionId: number,
  ): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/submit`,
      {},
    );
  }

  artistReleaseHistory(
    artistProfileId: number,
    submissionId: number,
  ): Observable<StatusHistoryEntry[]> {
    return this.http.get<StatusHistoryEntry[]>(
      `${this.publishingBase(artistProfileId)}/releases/${submissionId}/history`,
    );
  }
}
