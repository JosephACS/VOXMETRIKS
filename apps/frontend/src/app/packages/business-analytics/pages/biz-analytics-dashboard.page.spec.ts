import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { BizAnalyticsDashboardPage } from './biz-analytics-dashboard.page';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { BillingApiService } from '../../billing/services/billing-api.service';
import { CrmApiService } from '../../crm/services/crm-api.service';
import { SubscriptionsApiService } from '../../subscriptions/services/subscriptions-api.service';
import { CustomerSuccessApiService } from '../../customer-success/services/customer-success-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { StrategicOverview } from '../models/business-analytics.models';

describe('BizAnalyticsDashboardPage strategic AGG', () => {
  let fixture: ComponentFixture<BizAnalyticsDashboardPage>;
  let page: BizAnalyticsDashboardPage;

  const strategic: StrategicOverview = {
    organization_id: 1,
    period_start: '2026-08-01',
    period_end: '2026-08-09',
    include_global: false,
    comparable_periods: 1,
    objectives: Array.from({ length: 8 }).map((_, i) => ({
      objective_code: `OE-0${i + 1}`,
      title: `Objective ${i + 1}`,
      kpi:
        i === 3
          ? {
              objective_code: 'OE-04',
              kpi_code: 'campaign_roi',
              period_start: '2026-08-01',
              period_end: '2026-08-09',
              value: null,
              unit: 'ratio',
              source_label: 'campaigns:roi_snapshot',
              quality_status: 'roi_unavailable',
              is_synthetic: false,
              is_proxy: false,
              availability_status: 'unavailable',
              unavailable_reason: 'roi_attribution_missing',
              classification: 'unavailable',
            }
          : {
              objective_code: `OE-0${i + 1}`,
              kpi_code: 'active_members',
              period_start: '2026-08-01',
              period_end: '2026-08-09',
              value: i === 0 ? 3 : null,
              unit: 'count',
              source_label: 'organizations:membership',
              quality_status: i === 0 ? 'ok' : 'null_value',
              is_synthetic: false,
              is_proxy: false,
              availability_status: i === 0 ? 'available' : 'unavailable',
              classification: i === 0 ? 'real' : 'unavailable',
            },
      kpis: [],
      period_start: '2026-08-01',
      period_end: '2026-08-09',
      evidence_path: '/reports',
      report_path: '/reports',
      decision_path: '/business-decisions',
      trend: null,
      empty: i !== 0 && i !== 3 ? true : false,
    })),
    decision_capability: {
      can_create_decision: true,
      can_draft_report: true,
      can_refresh_strategic: true,
      is_ai: false,
      recommendation_mode: 'rule_based',
    },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BizAnalyticsDashboardPage],
      providers: [
        provideHttpClient(),
        provideRouter([]),
        {
          provide: BusinessAnalyticsApiService,
          useValue: {
            getStrategicOverview: () => of(strategic),
            getDashboard: () => of({ organization_id: 1, period: '2026-08-09', kpis: {} }),
            refreshStrategic: () => of({ rows_written: 8, period_start: '', period_end: '', include_global: false }),
          },
        },
        {
          provide: OrganizationContextService,
          useValue: {
            organizationId: () => 1,
            hasPermission: () => false,
          },
        },
        { provide: BillingApiService, useValue: { listInvoices: () => of({ items: [] }) } },
        { provide: CrmApiService, useValue: { listOpportunities: () => of({ items: [] }) } },
        { provide: SubscriptionsApiService, useValue: { listSubscriptions: () => of({ items: [] }) } },
        { provide: CustomerSuccessApiService, useValue: { listRisks: () => of([]) } },
        {
          provide: I18nService,
          useValue: {
            lang: () => 'es',
            t: (k: string) => k,
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(BizAnalyticsDashboardPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('renders eight objectives and strategic header', () => {
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('[data-testid="strategic-direction"]')).toBeTruthy();
    expect(root.querySelectorAll('[data-objective]').length).toBe(8);
    expect(root.textContent).toContain('Dirección estratégica');
    expect(page.strategic?.decision_capability.is_ai).toBe(false);
  });

  it('shows Sin datos for ROI without inventing zero', () => {
    const roi = page.strategic?.objectives.find((o) => o.objective_code === 'OE-04');
    expect(roi?.kpi?.value).toBeNull();
    expect(page.hasValue(roi!)).toBe(false);
    expect(page.statusLabel(roi!)).toBe('Sin datos');
    expect(page.formatKpiValue(roi!)).toBe('Sin datos');
  });

  it('does not expose trend with a single comparable period', () => {
    expect(page.strategic?.comparable_periods).toBe(1);
    for (const obj of page.strategic?.objectives || []) {
      expect(page.trendText(obj)).toBeNull();
    }
  });
});
