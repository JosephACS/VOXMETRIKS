import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';
import { I18nService } from '../../../core/services/i18n.service';
import {
  PlatformCatalogReviewsPage,
  apiStatusForQueueFilter,
} from './platform-catalog-reviews.page';

const BASE = environment.apiUrl;
const PLATFORM_REVIEWS = `${BASE}/platform/catalog-reviews`;

describe('PlatformCatalogReviewsPage filter mapping (051)', () => {
  let fixture: ComponentFixture<PlatformCatalogReviewsPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [PlatformCatalogReviewsPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        I18nService,
      ],
    })
      .overrideComponent(PlatformCatalogReviewsPage, {
        set: {
          imports: [CommonModule, FormsModule],
          template: `<div></div>`,
        },
      })
      .compileComponents();

    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(PlatformCatalogReviewsPage);
  });

  afterEach(() => {
    http.verify();
  });

  it('maps UI in_review bucket to canonical under_review for the API', () => {
    expect(apiStatusForQueueFilter('in_review')).toBe('under_review');
    expect(apiStatusForQueueFilter('submitted')).toBe('submitted');
    expect(apiStatusForQueueFilter('changes_requested')).toBe('changes_requested');
    expect(apiStatusForQueueFilter('approved')).toBe('approved');
    expect(apiStatusForQueueFilter('all')).toBeUndefined();
  });

  it('sends under_review when the En revisión filter is active', () => {
    const page = fixture.componentInstance;
    page.setFilter('in_review');

    const req = http.expectOne(
      (r) =>
        r.url === PLATFORM_REVIEWS &&
        r.params.get('status') === 'under_review' &&
        r.params.get('limit') === '100',
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('status')).not.toBe('in_review');
    req.flush([]);
  });

  it('omits status for the all filter', () => {
    fixture.detectChanges();
    const initial = http.expectOne(
      (r) => r.url === PLATFORM_REVIEWS && r.params.get('status') == null,
    );
    initial.flush([]);

    const page = fixture.componentInstance;
    page.setFilter('submitted');
    http.expectOne((r) => r.params.get('status') === 'submitted').flush([]);

    page.setFilter('all');
    const allReq = http.expectOne(
      (r) => r.url === PLATFORM_REVIEWS && r.params.get('status') == null,
    );
    allReq.flush([]);
  });
});
