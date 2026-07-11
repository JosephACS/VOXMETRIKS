import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { OrgSelectorComponent } from '../components/org-selector.component';
import { OrgNonePageComponent } from '../pages/org-none.page';
import { OrgCreatePageComponent } from '../pages/org-create.page';
import { OrgAcceptInvitePageComponent } from '../pages/org-accept-invite.page';
import { OrgAuditPageComponent } from '../pages/org-audit.page';
import { OrganizationContextService } from './organization-context.service';
import { OrganizationsApiService } from './organizations-api.service';
import { AuthService } from '../../../core/services/auth.service';

describe('OrgSelectorComponent (I4)', () => {
  let fixture: ComponentFixture<OrgSelectorComponent>;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OrgSelectorComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        OrganizationsApiService,
        OrganizationContextService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(OrgSelectorComponent);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('shows empty state and create option', async () => {
    fixture.detectChanges();
    const list = http.expectOne(`${base}/organizations`);
    const cur = http.expectOne(`${base}/organizations/current`);
    list.flush([]);
    cur.flush({ context: 'none' });
    await fixture.whenStable();
    fixture.detectChanges();
    const btn = fixture.nativeElement.querySelector('.org-selector-btn') as HTMLButtonElement;
    btn.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No hay organizaciones');
    expect(fixture.nativeElement.textContent).toContain('Crear organización');
  });
});

describe('OrgNonePageComponent (I4)', () => {
  it('keeps personal CTAs when user has no organization', async () => {
    await TestBed.configureTestingModule({
      imports: [OrgNonePageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        OrganizationsApiService,
        OrganizationContextService,
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(OrgNonePageComponent);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(`${environment.apiUrl}/organizations`).flush([]);
    http.expectOne(`${environment.apiUrl}/organizations/current`).flush({ context: 'none' });
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Sin organización empresarial');
    expect(text).toContain('Seguir en modo personal');
    expect(text).toContain('Crear organización');
    http.verify();
  });
});

describe('OrgCreatePageComponent (I4)', () => {
  it('blocks double submit and maps slug conflict', async () => {
    await TestBed.configureTestingModule({
      imports: [OrgCreatePageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        OrganizationsApiService,
        OrganizationContextService,
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(OrgCreatePageComponent);
    const http = TestBed.inject(HttpTestingController);
    const cmp = fixture.componentInstance;
    cmp.displayName = 'Dup';
    cmp.slug = 'dup';
    fixture.detectChanges();
    const p1 = cmp.submit();
    const p2 = cmp.submit();
    const reqs = http.match(`${environment.apiUrl}/organizations`);
    expect(reqs.length).toBe(1);
    reqs[0].flush(
      { status: 'error', message: 'Slug in use', details: { code: 'conflict' } },
      { status: 409, statusText: 'Conflict' },
    );
    await p1;
    await p2;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Conflicto de slug');
    http.verify();
  });
});

describe('OrgAcceptInvitePageComponent (I4)', () => {
  it('accepts token in memory and maps expired/gone', async () => {
    await TestBed.configureTestingModule({
      imports: [OrgAcceptInvitePageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        OrganizationsApiService,
        OrganizationContextService,
        { provide: AuthService, useValue: { isAuthenticated: () => true } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(OrgAcceptInvitePageComponent);
    const http = TestBed.inject(HttpTestingController);
    const cmp = fixture.componentInstance;
    fixture.detectChanges();
    cmp.token = 'gone-token';
    const p = cmp.accept();
    const req = http.expectOne(`${environment.apiUrl}/invitations/gone-token/accept`);
    req.flush(
      { status: 'error', message: 'Invitation expired', details: { code: 'invitation_gone' } },
      { status: 410, statusText: 'Gone' },
    );
    await p;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('no disponible');
    http.verify();
  });
});

describe('OrgAuditPageComponent sanitization (I4)', () => {
  it('summarizes audit without exposing token/hash keys', async () => {
    await TestBed.configureTestingModule({
      imports: [OrgAuditPageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        OrganizationsApiService,
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '1' } } },
        },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(OrgAuditPageComponent);
    const http = TestBed.inject(HttpTestingController);
    const cmp = fixture.componentInstance;
    fixture.detectChanges();
    const req = http.expectOne((r) => r.url.startsWith(`${environment.apiUrl}/organizations/1/audit-log`));
    req.flush({ items: [], page: 1, limit: 50, total: 0 });
    const summary = cmp.summarize({
      id: 1,
      action: 'invite.create',
      target_type: 'invitation',
      target_id: '1',
      source: 'api',
      result: 'ok',
      occurred_at: '2026-01-01T00:00:00Z',
      new_values: { email: 'a@b.com', token_hash: 'SECRET', invite_token: 'PLAIN' },
      previous_values: { password: 'x', status: 'pending' },
    });
    expect(summary).toContain('email');
    expect(summary).toContain('status');
    expect(summary).not.toContain('token');
    expect(summary).not.toContain('hash');
    expect(summary).not.toContain('password');
    expect(summary).not.toContain('SECRET');
    http.verify();
  });
});
