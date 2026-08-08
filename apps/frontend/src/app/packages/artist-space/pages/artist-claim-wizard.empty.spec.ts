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

describe('ArtistClaimWizardPage empty search (047)', () => {
  let pageFixture: ComponentFixture<ArtistClaimWizardPage>;
  let http: HttpTestingController;
  const base = environment.apiUrl;

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
            @if (searched() && !results().length) {
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
    expect(LOCALE_EN['artistSpace.claim.noResultsTitle']).not.toBe('Texto no disponible');

    const page = pageFixture.componentInstance;
    page.searchForm.setValue({ q: 'Artista Inexistente XYZ' });
    page.search();
    http
      .expectOne(
        (r) =>
          r.url.includes('/catalog/artists') &&
          r.params.get('search') === 'Artista Inexistente XYZ',
      )
      .flush({ items: [], total: 0 });
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
    expect(emptyText).toContain('Solicitar nuevo artista');

    const cta = empty!.querySelector('button.btn--primary') as HTMLButtonElement | null;
    expect(cta).toBeTruthy();
    cta!.click();
    pageFixture.detectChanges();
    expect(page.createForm.value.name).toBe('Artista Inexistente XYZ');
  });
});
