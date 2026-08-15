import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { PlatformOpsApiService } from './platform-ops-api.service';
import { environment } from '../../../../environments/environment';

describe('PlatformOpsApiService', () => {
  let service: PlatformOpsApiService;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(PlatformOpsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('getHealth hits GET /platform-ops/health', () => {
    service.getHealth().subscribe();
    const req = http.expectOne(`${base}/platform-ops/health`);
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'healthy', labeled_academic: true, message: 'ok', components: {} });
  });

  it('getOverview hits GET /platform-ops/overview', () => {
    service.getOverview().subscribe();
    const req = http.expectOne(`${base}/platform-ops/overview`);
    expect(req.request.method).toBe('GET');
    req.flush({
      health: 'healthy',
      generated_at: '2026-01-01T00:00:00Z',
      queues: [],
      next_queue: null,
      has_pending_work: false,
    });
  });

  it('listFlags hits GET /platform-ops/flags', () => {
    service.listFlags().subscribe();
    const req = http.expectOne(`${base}/platform-ops/flags`);
    req.flush([]);
  });
});
