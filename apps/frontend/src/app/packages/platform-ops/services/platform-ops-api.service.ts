import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  BackupRecord,
  BackgroundJob,
  FeatureFlag,
  HealthStatus,
  OperationalIncident,
  PlatformOpsOverview,
  ProviderConfig,
  UnresolvedAudioList,
} from '../models/platform-ops.models';
import { AudioSource } from '../../../shared/models/api.models';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class PlatformOpsApiService {
  private http = inject(HttpClient);

  getOverview(): Observable<PlatformOpsOverview> {
    return this.http.get<PlatformOpsOverview>(`${base}/platform-ops/overview`);
  }

  getHealth(): Observable<HealthStatus> {
    return this.http.get<HealthStatus>(`${base}/platform-ops/health`);
  }

  listProviders(): Observable<ProviderConfig[]> {
    return this.http.get<ProviderConfig[]>(`${base}/platform-ops/providers`);
  }

  listJobs(): Observable<BackgroundJob[]> {
    return this.http.get<BackgroundJob[]>(`${base}/platform-ops/jobs`);
  }

  listFlags(): Observable<FeatureFlag[]> {
    return this.http.get<FeatureFlag[]>(`${base}/platform-ops/flags`);
  }

  listBackups(): Observable<BackupRecord[]> {
    return this.http.get<BackupRecord[]>(`${base}/platform-ops/backups`);
  }

  listUnresolvedAudio(opts?: {
    q?: string;
    limit?: number;
    offset?: number;
  }): Observable<UnresolvedAudioList> {
    let params = new HttpParams();
    if (opts?.q) params = params.set('q', opts.q);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<UnresolvedAudioList>(`${base}/platform-ops/audio-unresolved`, {
      params,
    });
  }

  markAudioUnavailable(trackId: number, reason: string): Observable<AudioSource> {
    return this.http.post<AudioSource>(
      `${base}/platform-ops/audio-unresolved/${trackId}/unavailable`,
      { reason },
    );
  }

  reresolveAudio(trackId: number): Observable<AudioSource> {
    return this.http.post<AudioSource>(
      `${base}/platform-ops/audio-unresolved/${trackId}/reresolve`,
      {},
    );
  }

  listIncidents(): Observable<OperationalIncident[]> {
    return this.http.get<OperationalIncident[]>(`${base}/platform-ops/incidents`);
  }

  createIncident(body: {
    title: string;
    severity: string;
    description: string;
  }): Observable<OperationalIncident> {
    return this.http.post<OperationalIncident>(`${base}/platform-ops/incidents`, body);
  }

  resolveIncident(incidentId: number): Observable<OperationalIncident> {
    return this.http.post<OperationalIncident>(
      `${base}/platform-ops/incidents/${incidentId}/resolve`,
      {},
    );
  }
}
