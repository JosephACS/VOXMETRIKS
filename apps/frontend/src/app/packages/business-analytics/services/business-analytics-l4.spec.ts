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

  it('listKpis hits GET /business-analytics/kpis', () => {
    api.listKpis(1).subscribe();
    const req = http.expectOne(`${base}/business-analytics/kpis`);
    req.flush([]);
  });
});
