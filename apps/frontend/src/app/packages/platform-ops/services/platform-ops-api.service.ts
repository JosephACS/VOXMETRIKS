import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { BackupRecord, BackgroundJob, FeatureFlag, HealthStatus, ProviderConfig } from '../models/platform-ops.models';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class PlatformOpsApiService {
  private http = inject(HttpClient);

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
}
