import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api.service';
import {
  DashboardOverview,
  DeviceUsage,
  StreamsAnalytics,
} from '../models/enterprise-api.models';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly api = inject(ApiService);

  getOverview(): Observable<DashboardOverview> {
    return this.api.get<DashboardOverview>('/dashboard/overview');
  }

  getStreamAnalytics(startDate: string, endDate: string): Observable<StreamsAnalytics> {
    return this.api.get<StreamsAnalytics>('/analytics/streams', {
      start_date: startDate,
      end_date: endDate,
    });
  }

  getDeviceUsage(): Observable<DeviceUsage[]> {
    return this.getOverview().pipe(map((o) => o.device_usage ?? []));
  }
}
