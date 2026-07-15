import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ContributorCreateBody,
  DraftCreateBody,
  MetadataUpdateBody,
  PortalSummary,
  ReleaseDetail,
  ReleaseSubmission,
  StatusHistoryEntry,
  TrackCreateBody,
  ValidateReadyResult,
} from '../models/catalog-publishing.models';

const BASE = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class CatalogPublishingApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(orgId) });
  }

  // ── Artist portal ─────────────────────────────────────────────────────────

  portalSummary(orgId: number): Observable<PortalSummary> {
    return this.http.get<PortalSummary>(`${BASE}/artist-portal/summary`, {
      headers: this.orgHeaders(orgId),
    });
  }

  listPortalReleases(
    orgId: number,
    params?: { limit?: number; offset?: number },
  ): Observable<ReleaseSubmission[]> {
    let p = new HttpParams();
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    if (params?.offset != null) p = p.set('offset', String(params.offset));
    return this.http.get<ReleaseSubmission[]>(`${BASE}/artist-portal/releases`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  // ── Releases ──────────────────────────────────────────────────────────────

  listReleases(
    orgId: number,
    params?: { artist_profile_id?: number; limit?: number; offset?: number },
  ): Observable<ReleaseSubmission[]> {
    let p = new HttpParams();
    if (params?.artist_profile_id != null) {
      p = p.set('artist_profile_id', String(params.artist_profile_id));
    }
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    if (params?.offset != null) p = p.set('offset', String(params.offset));
    return this.http.get<ReleaseSubmission[]>(`${BASE}/releases`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  getRelease(orgId: number, submissionId: number): Observable<ReleaseDetail> {
    return this.http.get<ReleaseDetail>(`${BASE}/releases/${submissionId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  createDraft(orgId: number, body: DraftCreateBody): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(`${BASE}/releases`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  updateRelease(
    orgId: number,
    submissionId: number,
    body: MetadataUpdateBody,
  ): Observable<ReleaseSubmission> {
    return this.http.patch<ReleaseSubmission>(`${BASE}/releases/${submissionId}`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  addTrack(
    orgId: number,
    submissionId: number,
    body: TrackCreateBody,
  ): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${BASE}/releases/${submissionId}/tracks`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  updateTrack(
    orgId: number,
    submissionId: number,
    trackId: number,
    body: Partial<TrackCreateBody>,
  ): Observable<Record<string, unknown>> {
    return this.http.patch<Record<string, unknown>>(
      `${BASE}/releases/${submissionId}/tracks/${trackId}`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  reorderTracks(
    orgId: number,
    submissionId: number,
    ordered_track_ids: number[],
  ): Observable<unknown[]> {
    return this.http.post<unknown[]>(
      `${BASE}/releases/${submissionId}/tracks/reorder`,
      { ordered_track_ids },
      { headers: this.orgHeaders(orgId) },
    );
  }

  addContributor(
    orgId: number,
    submissionId: number,
    body: ContributorCreateBody,
  ): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${BASE}/releases/${submissionId}/contributors`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  uploadAudio(
    orgId: number,
    submissionId: number,
    trackId: number,
    file: File,
  ): Observable<Record<string, unknown>> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<Record<string, unknown>>(
      `${BASE}/releases/${submissionId}/tracks/${trackId}/audio`,
      fd,
      { headers: this.orgHeaders(orgId) },
    );
  }

  uploadCover(
    orgId: number,
    submissionId: number,
    file: File,
  ): Observable<Record<string, unknown>> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<Record<string, unknown>>(
      `${BASE}/releases/${submissionId}/cover`,
      fd,
      { headers: this.orgHeaders(orgId) },
    );
  }

  validateReady(orgId: number, submissionId: number): Observable<ValidateReadyResult> {
    return this.http.post<ValidateReadyResult>(
      `${BASE}/releases/${submissionId}/validate`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  submitRelease(orgId: number, submissionId: number): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(
      `${BASE}/releases/${submissionId}/submit`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  releaseHistory(orgId: number, submissionId: number): Observable<StatusHistoryEntry[]> {
    return this.http.get<StatusHistoryEntry[]>(`${BASE}/releases/${submissionId}/history`, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Catalog review ────────────────────────────────────────────────────────

  reviewQueue(
    orgId: number,
    params?: { limit?: number; offset?: number },
  ): Observable<ReleaseSubmission[]> {
    let p = new HttpParams();
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    if (params?.offset != null) p = p.set('offset', String(params.offset));
    return this.http.get<ReleaseSubmission[]>(`${BASE}/catalog-review/queue`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  reviewApprove(
    orgId: number,
    submissionId: number,
    notes = '',
  ): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(
      `${BASE}/catalog-review/${submissionId}/approve`,
      { notes },
      { headers: this.orgHeaders(orgId) },
    );
  }

  reviewReject(
    orgId: number,
    submissionId: number,
    reason: string,
  ): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(
      `${BASE}/catalog-review/${submissionId}/reject`,
      { reason },
      { headers: this.orgHeaders(orgId) },
    );
  }

  reviewRequestChanges(
    orgId: number,
    submissionId: number,
    notes: string,
  ): Observable<ReleaseSubmission> {
    return this.http.post<ReleaseSubmission>(
      `${BASE}/catalog-review/${submissionId}/request-changes`,
      { notes },
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── Media ─────────────────────────────────────────────────────────────────

  mediaContentUrl(mediaId: number): string {
    return `${BASE}/media/${mediaId}/content`;
  }
}
