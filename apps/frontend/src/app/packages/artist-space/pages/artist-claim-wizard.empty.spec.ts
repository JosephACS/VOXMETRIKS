import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';
import { LOCALE_EN } from '../../../core/i18n/locales/en';
import { I18nService } from '../../../core/services/i18n.service';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistClaimWizardPage } from './artist-claim-wizard.page';

describe('ArtistClaimWizardPage discovery (047 + 051)', () => {
  let pageFixture: ComponentFixture<ArtistClaimWizardPage>;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  function discoverRequest(query: string) {
    return http.expectOne(
      (r) => r.url === `${base}/artist-access/discover` && r.params.get('search') === query,
    );
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ArtistClaimWizardPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        ArtistSpaceApiService,
        I18nService,
        {
          provide: SpaceContextService,
          useValue: { bootstrap: () => Promise.resolve() },
        },
      ],
    })
      .overrideComponent(ArtistClaimWizardPage, {
        set: {
          // Avoid enterprise required signal-inputs under plain Vitest JIT.
          imports: [CommonModule, ReactiveFormsModule],
          template: `
            @if (searchError()) {
              <p data-testid="claim-search-error">{{ searchError() }}</p>
            } @else if (searched() && !results().length) {
              <div class="empty-state ent-empty" role="status" data-testid="claim-empty">
                <div class="ent-empty__title">{{ emptyTitle }}</div>
                <p class="ent-empty__description">{{ emptyBody }}</p>
                <button type="button" class="btn btn--primary" (click)="focusCreateNew()">
                  {{ emptyCta }}
                </button>
              </div>
            }
            <form [formGroup]="searchForm"></form>
            <form [formGroup]="createForm"></form>
          `,
        },
      })
      .compileComponents();

    const i18n = TestBed.inject(I18nService);
    pageFixture = TestBed.createComponent(ArtistClaimWizardPage);
    const page = pageFixture.componentInstance as ArtistClaimWizardPage & {
      emptyTitle: string;
      emptyBody: string;
      emptyCta: string;
    };
    page.emptyTitle = i18n.t('artistSpace.claim.noResultsTitle');
    page.emptyBody = i18n.t('artistSpace.claim.noResultsBody');
    page.emptyCta = i18n.t('artistSpace.claim.createNew');

    http = TestBed.inject(HttpTestingController);
    http.expectOne(`${base}/artist-access/requests/mine`).flush([]);
    pageFixture.detectChanges();
  });

  afterEach(() => {
    http?.verify();
  });

  it('renders real empty-state copy and prefills create form from query', () => {
    const i18n = TestBed.inject(I18nService);
    const title = i18n.t('artistSpace.claim.noResultsTitle');
    const body = i18n.t('artistSpace.claim.noResultsBody');
    const ctaLabel = i18n.t('artistSpace.claim.createNew');

    expect(title).toBe('No encontramos ese artista');
    expect(body).toBe('Prueba con otro nombre o solicita un perfil nuevo.');
    expect(title).not.toBe('Texto no disponible');
    expect(body).not.toBe('Texto no disponible');
    expect(ctaLabel).toBe('Solicitar nuevo artista');

    expect(LOCALE_EN['artistSpace.claim.noResultsTitle']).toBe("We couldn't find that artist");
    expect(LOCALE_EN['artistSpace.claim.noResultsBody']).toBe(
      'Try another name or request a new artist profile.',
    );

    const page = pageFixture.componentInstance;
    page.searchForm.setValue({ q: 'Artista Inexistente XYZ' });
    page.search();
    discoverRequest('Artista Inexistente XYZ').flush({ items: [], total: 0 });
    pageFixture.detectChanges();

    expect(page.searched()).toBe(true);
    expect(page.results().length).toBe(0);

    const empty = pageFixture.nativeElement.querySelector(
      '[data-testid="claim-empty"]',
    ) as HTMLElement | null;
    expect(empty).toBeTruthy();
    const emptyText = empty!.textContent ?? '';
    expect(emptyText).toContain('No encontramos ese artista');
    expect(emptyText).toContain('Prueba con otro nombre o solicita un perfil nuevo.');
    expect(emptyText).not.toContain('Texto no disponible');

    const cta = empty!.querySelector('button.btn--primary') as HTMLButtonElement | null;
    cta!.click();
    pageFixture.detectChanges();
    expect(page.createForm.value.name).toBe('Artista Inexistente XYZ');
    expect(page.mode()).toBe('create');
  });

  it('lets the server allowed_action drive the CTA instead of guessing', () => {
    const page = pageFixture.componentInstance;
    page.searchForm.setValue({ q: 'Nova' });
    page.search();
    discoverRequest('Nova').flush({
      items: [
        {
          warehouse_artist_id: 11,
          display_name: 'Nova Claim',
          artist_profile_id: null,
          management_state: 'unclaimed',
          allowed_action: 'claim_ownership',
        },
        {
          warehouse_artist_id: 12,
          display_name: 'Nova Managed',
          artist_profile_id: 5,
          management_state: 'managed',
          allowed_action: 'request_access',
        },
        {
          warehouse_artist_id: 13,
          display_name: 'Nova Pending',
          artist_profile_id: 6,
          management_state: 'managed',
          allowed_action: 'view_request',
        },
      ],
      total: 3,
    });

    const [claimable, managed, pending] = page.results();
    expect(page.actionLabelKey(claimable)).toBe('artistSpace.discovery.action.claimOwnership');
    expect(page.actionLabelKey(managed)).toBe('artistSpace.discovery.action.requestAccess');

    page.runAllowedAction(claimable);
    expect(page.pendingForm()).toBe('claim');

    page.runAllowedAction(managed);
    expect(page.pendingForm()).toBe('access');

    page.runAllowedAction(pending);
    expect(page.pendingForm()).toBeNull();
  });

  it('requires evidence for a claim and surfaces backend failures as errors', () => {
    const page = pageFixture.componentInstance;
    page.searchForm.setValue({ q: 'Nova' });
    page.search();
    discoverRequest('Nova').flush({
      items: [
        {
          warehouse_artist_id: 11,
          display_name: 'Nova Claim',
          artist_profile_id: null,
          management_state: 'unclaimed',
          allowed_action: 'claim_ownership',
        },
      ],
      total: 1,
    });

    page.runAllowedAction(page.results()[0]);
    page.submitClaim();
    http.expectNone(`${base}/artist-access/requests`);
    expect(page.error()).toBe(
      TestBed.inject(I18nService).t('artistSpace.claim.evidenceRequired'),
    );

    page.claimForm.patchValue({ evidence_url: 'https://example.com/nova' });
    page.submitClaim();
    const created = http.expectOne(`${base}/artist-access/requests`);
    expect(created.request.body).toMatchObject({
      request_type: 'claim_ownership',
      warehouse_artist_id: 11,
      evidence_url: 'https://example.com/nova',
      accuracy_attested: true,
    });

    created.flush(
      { detail: { code: 'artist_request_conflict' } },
      { status: 409, statusText: 'Conflict' },
    );

    // A failed request must never read as success.
    expect(page.message()).toBeNull();
    expect(page.error()).toBe(
      TestBed.inject(I18nService).t('artistSpace.error.requestConflict'),
    );
    expect(page.submitting()).toBe(false);
  });

  it('shows a retryable error instead of an empty result set when discovery fails', () => {
    const page = pageFixture.componentInstance;
    page.searchForm.setValue({ q: 'Nova' });
    page.search();
    discoverRequest('Nova').flush(
      { detail: 'boom' },
      { status: 500, statusText: 'Server Error' },
    );
    pageFixture.detectChanges();

    expect(page.searchError()).toBeTruthy();
    expect(page.results().length).toBe(0);
    expect(
      pageFixture.nativeElement.querySelector('[data-testid="claim-empty"]'),
    ).toBeNull();
  });
});
