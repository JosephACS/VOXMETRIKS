import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { CampaignsApiService } from './campaigns-api.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;
const orgId = 1;

describe('CampaignsApiService (L4)', () => {
  let api: CampaignsApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), CampaignsApiService],
    });
    api = TestBed.inject(CampaignsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('list hits GET /campaigns with org header', () => {
    api.list(orgId, { status: 'active' }).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/campaigns`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('X-Organization-Id')).toBe('1');
    req.flush({ items: [], total: 0, page: 1, page_size: 25 });
  });

  it('create hits POST /campaigns', () => {
    api.create(orgId, { name: 'Summer Push' }).subscribe();
    const req = http.expectOne(`${base}/campaigns`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.name).toBe('Summer Push');
    req.flush({ id: 1, name: 'Summer Push', status: 'draft' });
  });

  it('computeRoi hits POST /campaigns/1/roi/compute', () => {
    api.computeRoi(orgId, 1).subscribe();
    const req = http.expectOne(`${base}/campaigns/1/roi/compute`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, campaign_id: 1, status: 'unavailable', computed_at: '2026-01-01' });
  });

  it('lists attribution definitions and attributable revenue', () => {
    api.listAttributionDefinitions(orgId, 1).subscribe();
    const a = http.expectOne(`${base}/campaigns/1/attribution-definitions`);
    expect(a.request.method).toBe('GET');
    a.flush([]);

    api.listAttributableRevenue(orgId, 1).subscribe();
    const r = http.expectOne(`${base}/campaigns/1/attributable-revenue`);
    expect(r.request.method).toBe('GET');
    r.flush([]);
  });
});
