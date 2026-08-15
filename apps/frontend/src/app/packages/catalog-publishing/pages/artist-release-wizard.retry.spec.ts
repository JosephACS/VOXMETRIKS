import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  TestRequest,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';
import { I18nService } from '../../../core/services/i18n.service';
import { AuthService } from '../../../core/services/auth.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { ArtistContextService } from '../../artist-space/services/artist-context.service';
import { ArtistReleaseWizardPage } from './artist-release-wizard.page';

const BASE = environment.apiUrl;
const ORG_ID = 4;

/**
 * 051 — idempotent retry: persisted tracks/contributors must not duplicate,
 * and track metadata edits must PATCH existing rows.
 */
describe('ArtistReleaseWizardPage idempotent retry (051)', () => {
  let fixture: ComponentFixture<ArtistReleaseWizardPage>;
  let http: HttpTestingController;

  async function waitForRequest(url: string): Promise<TestRequest> {
    for (let i = 0; i < 100; i += 1) {
      const found = http.match((req) => req.url === url);
      if (found.length > 0) return found[0];
      await Promise.resolve();
      await new Promise<void>((resolve) => setTimeout(resolve, 0));
    }
    return http.expectOne((req) => req.url === url);
  }

  async function setup(): Promise<void> {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [ArtistReleaseWizardPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        I18nService,
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { data: { releaseContext: 'organization' } } },
        },
        {
          provide: AuthService,
          useValue: { getUser: () => ({ username: 'label.manager', preferences: {} }) },
        },
        {
          provide: OrganizationContextService,
          useValue: {
            organizationId: () => ORG_ID,
            hasPermission: (code: string) =>
              code === 'publishing.create' || code === 'publishing.view',
          },
        },
        {
          provide: ArtistContextService,
          useValue: {
            artistProfileId: () => null,
            displayName: () => null,
            can: () => false,
          },
        },
      ],
    })
      .overrideComponent(ArtistReleaseWizardPage, {
        set: {
          imports: [CommonModule, ReactiveFormsModule],
          template: `<form [formGroup]="form"></form>`,
        },
      })
      .compileComponents();

    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ArtistReleaseWizardPage);
    fixture.detectChanges();
    http
      .expectOne(
        (r) =>
          r.url === `${BASE}/artists` &&
          r.headers.get('X-Organization-Id') === String(ORG_ID),
      )
      .flush({
        items: [{ id: 31, display_name: 'First Act', status: 'active' }],
        total: 1,
      });
  }

  afterEach(() => {
    http?.verify();
  });

  it('retries only remaining contributors after a mid-list failure (no duplicates)', async () => {
    await setup();
    const page = fixture.componentInstance;
    page.form.patchValue({ title: 'Nocturno', artist_profile_id: 31 });
    page.tracks.at(0).patchValue({ title: 'Nocturno' });
    page.addContributor();
    page.addContributor();
    page.contributors.at(0).patchValue({ display_name: 'Alice', party_role: 'primary_artist' });
    page.contributors.at(1).patchValue({ display_name: 'Bob', party_role: 'featured' });

    const firstAttempt = page.onSubmit();
    (await waitForRequest(`${BASE}/releases`)).flush({
      id: 900,
      title: 'Nocturno',
      status: 'draft',
    });
    (await waitForRequest(`${BASE}/releases/900/tracks`)).flush({ id: 11 });

    const alice = await waitForRequest(`${BASE}/releases/900/contributors`);
    expect(alice.request.body.display_name).toBe('Alice');
    alice.flush({ id: 101 });

    const bobFail = await waitForRequest(`${BASE}/releases/900/contributors`);
    expect(bobFail.request.body.display_name).toBe('Bob');
    bobFail.flush({ detail: 'boom' }, { status: 500, statusText: 'Server Error' });
    await firstAttempt;

    expect(page.info()).toBeNull();
    expect(page.error()).toBeTruthy();
    expect(page.contributors.at(0).get('persisted_id')?.value).toBe(101);
    expect(page.contributors.at(1).get('persisted_id')?.value).toBeNull();
    expect(page.draftId()).toBe(900);

    const retry = page.onSubmit();
    (await waitForRequest(`${BASE}/releases/900`)).flush({
      id: 900,
      title: 'Nocturno',
      status: 'draft',
    });
    (await waitForRequest(`${BASE}/releases/900/tracks/11`)).flush({
      id: 11,
      title: 'Nocturno',
    });

    const onlyBob = await waitForRequest(`${BASE}/releases/900/contributors`);
    expect(onlyBob.request.body.display_name).toBe('Bob');
    onlyBob.flush({ id: 102 });
    await retry;

    expect(page.contributors.at(1).get('persisted_id')?.value).toBe(102);
    expect(page.info()).toBe(TestBed.inject(I18nService).t('publishing.wizard.draftSaved'));
    expect(page.error()).toBeNull();
  });

  it('PATCHes updateTrack when a persisted track title changes', async () => {
    await setup();
    const page = fixture.componentInstance;
    page.form.patchValue({ title: 'Nocturno', artist_profile_id: 31 });
    page.draftId.set(900);
    page.tracks.at(0).patchValue({
      title: 'Nocturno (remaster)',
      track_number: 1,
      isrc: 'USRC17607839',
      persisted_id: 11,
    });

    const pipeline = page.onSubmit();
    (await waitForRequest(`${BASE}/releases/900`)).flush({
      id: 900,
      title: 'Nocturno',
      status: 'draft',
    });

    const patch = await waitForRequest(`${BASE}/releases/900/tracks/11`);
    expect(patch.request.method).toBe('PATCH');
    expect(patch.request.body).toEqual({
      title: 'Nocturno (remaster)',
      track_number: 1,
      isrc: 'USRC17607839',
    });
    patch.flush({ id: 11 });
    await pipeline;

    expect(page.info()).toBe(TestBed.inject(I18nService).t('publishing.wizard.draftSaved'));
    expect(page.error()).toBeNull();
  });

  it('keeps info null and sets error when a late step fails', async () => {
    await setup();
    const page = fixture.componentInstance;
    page.form.patchValue({ title: 'Nocturno', artist_profile_id: 31 });
    page.tracks.at(0).patchValue({ title: 'Nocturno' });

    const pipeline = page.onSubmit();
    (await waitForRequest(`${BASE}/releases`)).flush({
      id: 901,
      title: 'Nocturno',
      status: 'draft',
    });
    (
      await waitForRequest(`${BASE}/releases/901/tracks`)
    ).flush({ detail: 'track failed' }, { status: 400, statusText: 'Bad Request' });
    await pipeline;

    expect(page.info()).toBeNull();
    expect(page.error()).toBeTruthy();
    expect(page.busy()).toBe(false);
    expect(page.draftId()).toBe(901);
  });
});
