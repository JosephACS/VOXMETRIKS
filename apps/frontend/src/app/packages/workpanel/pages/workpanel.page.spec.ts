import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { WorkpanelPage } from './workpanel.page';
import { WorkpanelApiService, WorkpanelResponse } from '../services/workpanel-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

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
                'workpanel.notice.syntheticFallback':
                  'Incluye datos sintéticos del warehouse (pruebas analíticas).',
                'workpanel.notice.simulatedAmounts':
                  'Importes académicos/simulados — no representan cobros reales.',
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
      ],
    });
    fixture = TestBed.createComponent(WorkpanelPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('shows exactly one role=status when synthetic + simulated', () => {
    page.data = baseResponse({
      includes_synthetic_events: true,
      data_classification: 'synthetic',
      monetary_classification: 'simulated',
      classification_note: 'Nota sintética de prueba.',
    });
    fixture.detectChanges();

    const notice = page.dataNotice;
    expect(notice).toBeTruthy();
    expect(notice).toContain('Nota sintética de prueba.');
    expect(notice).toContain('Importes académicos/simulados');
    expect(notice).toContain('simulados');

    const statuses = fixture.nativeElement.querySelectorAll('.wp-chip[role="status"]');
    expect(statuses.length).toBe(1);
    expect(statuses[0].textContent).toContain('Nota sintética de prueba.');
    expect(statuses[0].textContent).toContain('Importes académicos/simulados');
  });

  it('hides the notice when classifications are absent', () => {
    page.data = baseResponse({
      includes_synthetic_events: false,
      data_classification: 'real',
      monetary_classification: 'real',
    });
    fixture.detectChanges();

    expect(page.dataNotice).toBeNull();
    expect(fixture.nativeElement.querySelectorAll('.wp-chip[role="status"]').length).toBe(0);
  });
});
