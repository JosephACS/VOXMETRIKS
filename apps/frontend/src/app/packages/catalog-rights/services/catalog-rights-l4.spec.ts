import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { CatalogRightsApiService } from './catalog-rights-api.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;
const orgId = 1;

describe('CatalogRightsApiService (L4)', () => {
  let api: CatalogRightsApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), CatalogRightsApiService],
    });
    api = TestBed.inject(CatalogRightsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('listAssets hits GET /catalog-rights/assets with org header', () => {
    let result: unknown;
    api.listAssets(orgId, { status: 'active' }).subscribe((r) => (result = r));
    const req = http.expectOne((r) => r.url === `${base}/catalog-rights/assets`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('X-Organization-Id')).toBe('1');
    expect(req.request.params.get('status')).toBe('active');
    req.flush({ items: [], total: 0, page: 1, page_size: 25 });
    expect((result as { total: number }).total).toBe(0);
  });

  it('registerAsset hits POST /catalog-rights/assets', () => {
    api.registerAsset(orgId, { title: 'Song A' }).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/assets`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.title).toBe('Song A');
    req.flush({ id: 1, title: 'Song A', status: 'active' });
  });

  it('linkWarehouseTrack hits POST /catalog-rights/assets/1/link-warehouse-track', () => {
    api.linkWarehouseTrack(orgId, 1, 42).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/assets/1/link-warehouse-track`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.warehouse_track_id).toBe(42);
    req.flush({ id: 1, warehouse_track_id: 42 });
  });

  it('detectOverlap hits POST /catalog-rights/assets/1/detect-overlap', () => {
    api.detectOverlap(orgId, 1, 'master').subscribe();
    const req = http.expectOne(`${base}/catalog-rights/assets/1/detect-overlap`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.rights_type).toBe('master');
    req.flush([]);
  });

  it('createRelease hits POST /catalog-rights/releases', () => {
    api.createRelease(orgId, { title: 'Album A' }).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/releases`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.title).toBe('Album A');
    req.flush({ id: 1, title: 'Album A' });
  });

  it('listContracts hits GET /catalog-rights/contracts with asset filter', () => {
    api.listContracts(orgId, { asset_id: 7 }).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/catalog-rights/contracts`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('asset_id')).toBe('7');
    req.flush({ items: [], total: 0, page: 1, page_size: 25 });
  });

  it('createContract hits POST /catalog-rights/contracts', () => {
    api
      .createContract(orgId, { asset_id: 1, rights_type: 'master', valid_from: '2026-01-01' })
      .subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.rights_type).toBe('master');
    req.flush({ id: 1, asset_id: 1, rights_type: 'master', status: 'draft' });
  });

  it('addContractParty hits POST /catalog-rights/contracts/1/parties', () => {
    api
      .addContractParty(orgId, 1, { party_name: 'Party A', ownership_percentage: 50 })
      .subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/parties`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.ownership_percentage).toBe(50);
    req.flush({ party: { id: 1, party_name: 'Party A' }, conflicts_opened: [] });
  });

  it('setTerritories hits POST /catalog-rights/contracts/1/territories', () => {
    api.setTerritories(orgId, 1, [{ territory_code: 'US', territory_name: 'United States' }]).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/territories`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.territories[0].territory_code).toBe('US');
    req.flush({ territories: [], conflicts_opened: [] });
  });

  it('setAuthorizedUses hits POST /catalog-rights/contracts/1/authorized-uses', () => {
    api.setAuthorizedUses(orgId, 1, [{ use_code: 'streaming' }]).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/authorized-uses`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.uses[0].use_code).toBe('streaming');
    req.flush([]);
  });

  it('submitForApproval hits POST /catalog-rights/contracts/1/submit-for-approval', () => {
    api.submitForApproval(orgId, 1).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/submit-for-approval`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, status: 'pending' });
  });

  it('approveContract hits POST /catalog-rights/contracts/1/approve', () => {
    api.approveContract(orgId, 1, true, 'looks good').subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/approve`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.approved).toBe(true);
    req.flush({ id: 1, status: 'approved' });
  });

  it('archiveContract hits POST /catalog-rights/contracts/1/archive', () => {
    api.archiveContract(orgId, 1, 'no longer needed').subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/archive`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.reason).toBe('no longer needed');
    req.flush({ id: 1, status: 'archived' });
  });

  it('getContractHistory hits GET /catalog-rights/contracts/1/history', () => {
    api.getContractHistory(orgId, 1).subscribe();
    const req = http.expectOne(`${base}/catalog-rights/contracts/1/history`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('listConflicts hits GET /catalog-rights/conflicts', () => {
    api.listConflicts(orgId, { status: 'open' }).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/catalog-rights/conflicts`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('status')).toBe('open');
    req.flush([]);
  });

  it('openConflict hits POST /catalog-rights/conflicts', () => {
    api
      .openConflict(orgId, { asset_id: 1, rights_type: 'master', territory_code: 'US' })
      .subscribe();
    const req = http.expectOne(`${base}/catalog-rights/conflicts`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.territory_code).toBe('US');
    req.flush({ id: 1, status: 'open' });
  });

  it('resolveConflict hits POST /catalog-rights/conflicts/1/resolve', () => {
    api.resolveConflict(orgId, 1, 'resolved', 'renegotiated').subscribe();
    const req = http.expectOne(`${base}/catalog-rights/conflicts/1/resolve`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.resolution).toBe('resolved');
    req.flush({ id: 1, status: 'resolved' });
  });
});
