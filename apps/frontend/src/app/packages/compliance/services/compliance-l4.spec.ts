import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComplianceApiService } from './compliance-api.service';
import { environment } from '../../../../environments/environment';

describe('ComplianceApiService', () => {
  let service: ComplianceApiService;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(ComplianceApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listTerms hits GET /compliance/terms with org header', () => {
    service.listTerms(5).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/compliance/terms`);
    expect(req.request.headers.get('X-Organization-Id')).toBe('5');
    req.flush({ items: [], total: 0 });
  });

  it('submitDsr hits POST /compliance/dsr', () => {
    service.submitDsr(5, { request_type: 'export' }).subscribe();
    const req = http.expectOne(`${base}/compliance/dsr`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, request_type: 'export', status: 'submitted' });
  });
});
