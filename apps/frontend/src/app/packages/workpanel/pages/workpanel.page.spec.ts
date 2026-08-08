import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { WorkpanelPage } from './workpanel.page';
import { WorkpanelApiService, WorkpanelResponse } from '../services/workpanel-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { SimpleReportsApiService } from '../../simple-reports/services/simple-reports-api.service';

const SYNTHETIC_FALLBACK =
  'Incluye datos sintéticos del warehouse (pruebas analíticas).';
const SIMULATED_AMOUNTS =
  'Importes académicos/simulados — no representan cobros reales.';
const COMBINED_COMPACT =
  'Datos sintéticos de demostración; importes académicos/simulados (no cobros reales).';

function baseResponse(overrides: Partial<WorkpanelResponse> = {}): WorkpanelResponse {
  return {
    title: 'Workpanel',
    subtitle: '',
    period: '2026-01',
    period_start: '2026-01-01',
    period_end_exclusive: '2026-02-01',
    updated_at: '2026-01-01T00:00:00Z',
    analytics_updated_at: null,
    includes_synthetic_events: false,
    data_classification: 'real',
    monetary_classification: 'real',
    classification_note: null,
    available_periods: ['2026-01'],
    default_period: '2026-01',
    sections: [],
    metrics: [],
    pendings: [],
    links: [],
    ...overrides,
  };
}

describe('WorkpanelPage data notice', () => {
  let page: WorkpanelPage;
  let fixture: ReturnType<typeof TestBed.createComponent<WorkpanelPage>>;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [WorkpanelPage],
      providers: [
        provideRouter([]),
        {
          provide: OrganizationContextService,
          useValue: { organizationId: () => 1 },
        },
        {
          provide: I18nService,
          useValue: {
            lang: () => 'es' as const,
            t: (k: string) => {
              const map: Record<string, string> = {
                'workpanel.notice.syntheticFallback': SYNTHETIC_FALLBACK,
                'workpanel.notice.simulatedAmounts': SIMULATED_AMOUNTS,
                'workpanel.notice.combinedCompact': COMBINED_COMPACT,
              };
              return map[k] ?? k;
            },
          },
        },
        {
          provide: WorkpanelApiService,
          useValue: {
            get: () => of(baseResponse()),
          },
        },
        {
          provide: SimpleReportsApiService,
          useValue: {
            catalog: () =>
              of({
                items: [
                  {
                    id: 'r1',
                    title: 'Reporte demo',
                    category: 'ops',
                    module: 'control_decision',
                  },
                ],
              }),
          },
        },
      ],
    });
    fixture = TestBed.createComponent(WorkpanelPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  function applyData(overrides: Partial<WorkpanelResponse>): void {
    page.data = baseResponse(overrides);
    page.loading = false;
    page.error = '';
    fixture.detectChanges();
  }

  function expectSingleStatus(contains: string | RegExp): void {
    const statuses = fixture.nativeElement.querySelectorAll('[role="status"]');
    expect(statuses.length).toBe(1);
    const text = statuses[0].textContent || '';
    if (typeof contains === 'string') {
      expect(text).toContain(contains);
    } else {
      expect(text).toMatch(contains);
    }
  }

  it('appends simulatedAmounts when note only mentions synthetic', () => {
    applyData({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'simulated',
      classification_note: 'Incluye datos sintéticos del warehouse.',
    });

    const notice = page.dataNotice!;
    expect(notice).toContain('sintéticos');
    expect(notice).toContain(SIMULATED_AMOUNTS);
    expect((notice.match(/académicos\/simulados/gi) || []).length).toBe(1);
    expectSingleStatus('sintéticos');
  });

  it('appends syntheticFallback when note only mentions simulated amounts', () => {
    applyData({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'simulated',
      classification_note: 'Importes académicos/simulados en este periodo.',
    });

    const notice = page.dataNotice!;
    expect(notice).toContain('académicos/simulados');
    expect(notice).toContain(SYNTHETIC_FALLBACK);
    expect((notice.match(/académicos\/simulados/gi) || []).length).toBe(1);
    expect((notice.match(/sintéticos/gi) || []).length).toBe(1);
    expectSingleStatus('sintéticos');
  });

  it('returns the note once when it already mentions both classifications', () => {
    const both =
      'Nota sintética de prueba con importes académicos/simulados.';
    applyData({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'simulated',
      classification_note: both,
    });

    expect(page.dataNotice).toBe(both);
    expectSingleStatus(both);
  });

  it('uses combinedCompact when both classifications and note is absent', () => {
    applyData({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'simulated',
      classification_note: null,
    });

    expect(page.dataNotice).toBe(COMBINED_COMPACT);
    expectSingleStatus('académicos/simulados');
  });

  it('shows syntheticFallback (or note) for synthetic only', () => {
    applyData({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'real',
      classification_note: null,
    });

    expect(page.dataNotice).toBe(SYNTHETIC_FALLBACK);
    expect(page.dataNotice).not.toContain('académicos');
    expectSingleStatus('sintéticos');
  });

  it('shows simulatedAmounts for simulated only', () => {
    applyData({
      includes_synthetic_events: false,
      data_classification: 'real',
      monetary_classification: 'simulated',
      classification_note: null,
    });

    expect(page.dataNotice).toBe(SIMULATED_AMOUNTS);
    expect(page.dataNotice).not.toContain('sintéticos');
    expectSingleStatus('académicos/simulados');
  });

  it('keeps a single role=status when pendings are empty', () => {
    applyData({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'simulated',
      classification_note: null,
      pendings: [],
    });

    expect(fixture.nativeElement.querySelectorAll('[role="status"]').length).toBe(1);
    expect(fixture.nativeElement.querySelector('.wp-empty')?.textContent).toContain(
      'Sin pendientes críticos',
    );
  });

  it('exposes Reportes relacionados only via related-reports-panel', () => {
    applyData({
      includes_synthetic_events: false,
      data_classification: 'real',
      monetary_classification: 'real',
      pendings: [],
    });

    const regions = Array.from(
      fixture.nativeElement.querySelectorAll('[aria-label="Reportes relacionados"]'),
    ) as HTMLElement[];
    expect(regions.length).toBe(1);
    expect(regions[0].classList.contains('related')).toBe(true);

    const headings = Array.from(
      fixture.nativeElement.querySelectorAll('h2') as NodeListOf<HTMLElement>,
    ).filter((h) => (h.textContent || '').trim().includes('Reportes relacionados'));
    expect(headings.length).toBe(1);
  });

  it('hides the notice when classifications are absent', () => {
    applyData({
      includes_synthetic_events: false,
      data_classification: 'real',
      monetary_classification: 'real',
    });

    expect(page.dataNotice).toBeNull();
    expect(fixture.nativeElement.querySelectorAll('[role="status"]').length).toBe(0);
  });
});
