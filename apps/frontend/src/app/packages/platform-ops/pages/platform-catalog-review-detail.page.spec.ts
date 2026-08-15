import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';
import { I18nService } from '../../../core/services/i18n.service';
import { PlatformCatalogReviewDetailPage } from './platform-catalog-review-detail.page';

const BASE = environment.apiUrl;
const DETAIL_URL = `${BASE}/platform/catalog-reviews/42`;
const REQUEST_CHANGES_URL = `${BASE}/platform/catalog-reviews/42/request-changes`;

describe('PlatformCatalogReviewDetailPage requestChanges (051)', () => {
  let fixture: ComponentFixture<PlatformCatalogReviewDetailPage>;
  let http: HttpTestingController;
  let i18n: I18nService;

  beforeEach(async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [PlatformCatalogReviewDetailPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        I18nService,
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '42' } } },
        },
      ],
    })
      .overrideComponent(PlatformCatalogReviewDetailPage, {
        set: {
          imports: [CommonModule, FormsModule],
          template: `<div></div>`,
        },
      })
      .compileComponents();

    http = TestBed.inject(HttpTestingController);
    i18n = TestBed.inject(I18nService);
    await i18n.ensureEnterpriseEs();
    fixture = TestBed.createComponent(PlatformCatalogReviewDetailPage);
    fixture.detectChanges();
    http.expectOne(DETAIL_URL).flush({
      submission: { id: 42, title: 'Demo', status: 'under_review', release_type: 'single' },
      tracks: [],
      contributors: [],
      issues: [],
      history: [],
    });
  });

  afterEach(() => {
    http.verify();
  });

  it('requires a non-empty note and does not call the API when notes are blank', () => {
    const page = fixture.componentInstance;
    page.notes = '   ';
    page.requestChanges();

    http.expectNone(REQUEST_CHANGES_URL);
    expect(page.actionError()).toBe(i18n.t('publishing.review.notesRequired'));
    expect(page.info()).toBeNull();
    expect(page.busy()).toBe(false);
  });

  it('posts trimmed notes when requesting changes', () => {
    const page = fixture.componentInstance;
    page.notes = '  please fix artwork  ';
    page.requestChanges();

    const req = http.expectOne(REQUEST_CHANGES_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ notes: 'please fix artwork' });
    expect(req.request.body.notes).not.toBe('changes requested');
    req.flush({ id: 42, status: 'changes_requested' });
    http.expectOne(DETAIL_URL).flush({
      submission: {
        id: 42,
        title: 'Demo',
        status: 'changes_requested',
        release_type: 'single',
      },
      tracks: [],
      contributors: [],
      issues: [],
      history: [],
    });

    expect(page.actionError()).toBeNull();
    expect(page.info()).toBe(i18n.t('publishing.review.changesRequested'));
  });
});
