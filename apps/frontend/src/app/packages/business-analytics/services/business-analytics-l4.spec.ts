import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BusinessAnalyticsApiService } from './business-analytics-api.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;

describe('BusinessAnalyticsApiService (L4)', () => {
  let api: BusinessAnalyticsApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), BusinessAnalyticsApiService],
    });
    api = TestBed.inject(BusinessAnalyticsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('getDashboard hits GET /business-analytics/dashboard', () => {
    api.getDashboard(1).subscribe();
    const req = http.expectOne(`${base}/business-analytics/dashboard`);
    expect(req.request.headers.get('X-Organization-Id')).toBe('1');
    req.flush({ organization_id: 1, period: '2026-01-01', kpis: {} });
  });

  it('getStrategicOverview hits GET /business-analytics/strategic/overview', () => {
    api.getStrategicOverview(7, false).subscribe();
    const req = http.expectOne(
      (r) =>
        r.url === `${base}/business-analytics/strategic/overview` &&
        r.params.get('include_global') === 'false',
    );
    expect(req.request.headers.get('X-Organization-Id')).toBe('7');
    req.flush({
      organization_id: 7,
      period_start: '2026-08-01',
      period_end: '2026-08-09',
      include_global: false,
      comparable_periods: 1,
      objectives: Array.from({ length: 8 }).map((_, i) => ({
        objective_code: `OE-0${i + 1}`,
        title: `Obj ${i + 1}`,
        kpis: [],
        period_start: '2026-08-01',
        period_end: '2026-08-09',
        empty: true,
      })),
      decision_capability: {
        can_create_decision: false,
        can_draft_report: true,
        can_refresh_strategic: true,
        is_ai: false,
        recommendation_mode: 'rule_based',
      },
    });
  });

  it('refreshStrategic hits POST /business-analytics/strategic/refresh', () => {
    api.refreshStrategic(3).subscribe();
    const req = http.expectOne(
      (r) =>
        r.method === 'POST' &&
        r.url === `${base}/business-analytics/strategic/refresh`,
    );
    expect(req.request.headers.get('X-Organization-Id')).toBe('3');
    req.flush({
      organization_id: 3,
      period_start: '2026-08-01',
      period_end: '2026-08-09',
      include_global: false,
      rows_written: 12,
    });
  });

  it('listKpis hits GET /business-analytics/kpis', () => {
    api.listKpis(1).subscribe();
    const req = http.expectOne(`${base}/business-analytics/kpis`);
    req.flush([]);
  });
});
