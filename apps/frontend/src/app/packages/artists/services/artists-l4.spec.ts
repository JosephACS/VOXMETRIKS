import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ArtistsApiService } from './artists-api.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;
const orgId = 1;

describe('ArtistsApiService (L4)', () => {
  let api: ArtistsApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), ArtistsApiService],
    });
    api = TestBed.inject(ArtistsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('list hits GET /artists with org header', () => {
    let result: unknown;
    api.list(orgId, { status: 'active' }).subscribe((r) => (result = r));
    const req = http.expectOne((r) => r.url === `${base}/artists`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('X-Organization-Id')).toBe('1');
    expect(req.request.params.get('status')).toBe('active');
    req.flush({ items: [], total: 0, page: 1, page_size: 25 });
    expect((result as { total: number }).total).toBe(0);
  });

  it('create hits POST /artists', () => {
    let result: unknown;
    api.create(orgId, { display_name: 'New Artist' }).subscribe((r) => (result = r));
    const req = http.expectOne(`${base}/artists`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.display_name).toBe('New Artist');
    req.flush({ id: 1, display_name: 'New Artist', status: 'draft' });
    expect((result as { status: string }).status).toBe('draft');
  });

  it('get hits GET /artists/1', () => {
    api.get(orgId, 1).subscribe();
    const req = http.expectOne(`${base}/artists/1`);
    expect(req.request.method).toBe('GET');
    req.flush({ id: 1, display_name: 'Artist', status: 'draft' });
  });

  it('activate hits POST /artists/1/activate', () => {
    api.activate(orgId, 1, 'go live').subscribe();
    const req = http.expectOne(`${base}/artists/1/activate`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.reason).toBe('go live');
    req.flush({ id: 1, status: 'active' });
  });

  it('linkWarehouseArtist hits POST /artists/1/link-warehouse', () => {
    api.linkWarehouseArtist(orgId, 1, 42).subscribe();
    const req = http.expectOne(`${base}/artists/1/link-warehouse`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.warehouse_artist_id).toBe(42);
    req.flush({ id: 1, warehouse_artist_id: 42 });
  });

  it('transferOrganization hits POST /artists/1/transfer', () => {
    api.transferOrganization(orgId, 1, 999, 'ownership change').subscribe();
    const req = http.expectOne(`${base}/artists/1/transfer`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.target_organization_id).toBe(999);
    req.flush({ id: 1, organization_id: 999 });
  });

  it('getHistory hits GET /artists/1/history', () => {
    api.getHistory(orgId, 1).subscribe();
    const req = http.expectOne(`${base}/artists/1/history`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('assignManager hits POST /artists/1/assignments', () => {
    api.assignManager(orgId, 1, 7, 'manager').subscribe();
    const req = http.expectOne(`${base}/artists/1/assignments`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.user_id).toBe(7);
    req.flush({ id: 1, user_id: 7, role: 'manager', status: 'active' });
  });

  it('addTeamMember hits POST /artists/1/team', () => {
    api.addTeamMember(orgId, 1, 8, 'producer').subscribe();
    const req = http.expectOne(`${base}/artists/1/team`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.team_role).toBe('producer');
    req.flush({ id: 1, user_id: 8, team_role: 'producer', status: 'active' });
  });

  it('setExternalIdentifier hits POST /artists/1/external-identifiers', () => {
    api.setExternalIdentifier(orgId, 1, 'spotify', 'spotify-id-1').subscribe();
    const req = http.expectOne(`${base}/artists/1/external-identifiers`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.system_code).toBe('spotify');
    req.flush({ id: 1, system_code: 'spotify', external_value: 'spotify-id-1' });
  });
});
