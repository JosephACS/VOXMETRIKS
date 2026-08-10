import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { ReportingApiService } from './reporting-api.service';

const base = environment.apiUrl;

describe('ReportingApiService', () => {
  let api: ReportingApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), ReportingApiService],
    });
    api = TestBed.inject(ReportingApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('cancels a decision with organization scope', () => {
    api.cancelDecision(12, 34, 'Insufficient evidence').subscribe();

    const req = http.expectOne(`${base}/business-decisions/34/cancel`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Organization-Id')).toBe('12');
    expect(req.request.body).toEqual({ reason: 'Insufficient evidence' });
    req.flush({ id: 34, organization_id: 12, title: 'Decision', proposal: 'Proposal', status: 'canceled' });
  });
});
