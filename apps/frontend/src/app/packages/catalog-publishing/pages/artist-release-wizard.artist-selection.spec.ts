import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
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
 * 051 · T004 — the organization catalog manages many artists, so the wizard must
 * never publish against "the first profile it can find".
 */
describe('ArtistReleaseWizardPage explicit artist selection (051)', () => {
  let fixture: ComponentFixture<ArtistReleaseWizardPage>;
  let http: HttpTestingController;

  async function setup(context: 'organization' | 'artist'): Promise<void> {
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
          useValue: { snapshot: { data: { releaseContext: context } } },
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
          // Enterprise UI uses required signal inputs; the logic under test is the form.
          imports: [CommonModule, ReactiveFormsModule],
          template: `<form [formGroup]="form"></form>`,
        },
      })
      .compileComponents();

    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ArtistReleaseWizardPage);
    fixture.detectChanges();
  }

  afterEach(() => {
    http?.verify();
  });

  function flushOrgArtists(): void {
    http
      .expectOne(
        (r) =>
          r.url === `${BASE}/artists` &&
          r.headers.get('X-Organization-Id') === String(ORG_ID),
      )
      .flush({
        items: [
          { id: 31, display_name: 'First Act', status: 'active' },
          { id: 32, display_name: 'Second Act', status: 'active' },
        ],
        total: 2,
      });
  }

  it('blocks submission until an artist is chosen and uses exactly that artist', async () => {
    await setup('organization');
    flushOrgArtists();

    const page = fixture.componentInstance;
    page.form.patchValue({ title: 'Nocturno' });
    page.tracks.at(0).patchValue({ title: 'Nocturno' });

    expect(page.orgArtists().length).toBe(2);
    expect(page.form.controls.artist_profile_id.hasError('required')).toBe(true);
    expect(page.form.invalid).toBe(true);

    page.onSubmit();
    http.expectNone(`${BASE}/releases`);

    page.form.patchValue({ artist_profile_id: 32 });
    expect(page.form.valid).toBe(true);

    const pipeline = page.onSubmit();
    const created = http.expectOne(`${BASE}/releases`);
    expect(created.request.body.artist_profile_id).toBe(32);
    expect(created.request.body.artist_profile_id).not.toBe(31);
    created.flush({ id: 900, title: 'Nocturno', status: 'draft' });
    await fixture.whenStable();

    const trackRequest = http.expectOne(`${BASE}/releases/900/tracks`);
    expect(trackRequest.request.body.title).toBe('Nocturno');
    trackRequest.flush({ id: 1 });
    await pipeline;

    expect(page.info()).toBe(TestBed.inject(I18nService).t('publishing.wizard.draftSaved'));
    expect(page.error()).toBeNull();
  });

  it('stops the wizard with an error instead of a false success when the draft fails', async () => {
    await setup('organization');
    flushOrgArtists();

    const page = fixture.componentInstance;
    page.form.patchValue({ title: 'Nocturno', artist_profile_id: 31 });
    page.tracks.at(0).patchValue({ title: 'Nocturno' });

    const pipeline = page.onSubmit();
    http
      .expectOne(`${BASE}/releases`)
      .flush({ detail: 'nope' }, { status: 400, statusText: 'Bad Request' });
    await pipeline;

    expect(page.error()).toBeTruthy();
    expect(page.info()).toBeNull();
    expect(page.draftId()).toBeNull();
    expect(page.busy()).toBe(false);
  });

  it('refuses to open the artist-space wizard without an active artist', async () => {
    await setup('artist');
    const page = fixture.componentInstance;
    expect(page.contextError()).toBe(
      TestBed.inject(I18nService).t('artistSpace.error.noActiveArtist'),
    );
    expect(page.canSubmitRelease()).toBe(false);
  });
});
