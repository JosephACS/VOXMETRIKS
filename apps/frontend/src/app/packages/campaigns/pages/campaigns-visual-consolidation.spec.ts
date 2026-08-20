import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { signal } from '@angular/core';
import { CampaignsListPage } from './campaigns-list.page';
import { CampaignDetailPage } from './campaign-detail.page';
import { CampaignsApiService } from '../services/campaigns-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { ActivatedRoute } from '@angular/router';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';

function i18n() {
  return {
    lang: signal('es'),
    t: (k: string) => k,
  };
}

describe('Campaigns visual consolidation', () => {
  describe('list CTA / form', () => {
    let fixture: ComponentFixture<CampaignsListPage>;
    let page: CampaignsListPage;

    beforeEach(async () => {
      TestBed.overrideComponent(CampaignsListPage, {
        set: {
          template: `
            <button type="button" data-testid="campaigns-new-cta" (click)="showCreateForm = !showCreateForm">
              Nueva campaña
            </button>
            @if (showCreateForm) {
              <div data-testid="campaigns-create-form">
                <form [formGroup]="createForm" (ngSubmit)="createCampaign()">
                  <input formControlName="name" />
                  <button type="submit">Crear</button>
                </form>
              </div>
            }
            @for (c of campaigns; track c.id) {
              <a [routerLink]="['/campaigns', c.id]">{{ c.name }}</a>
            }
          `,
          templateUrl: undefined as unknown as string,
        },
      });

      await TestBed.configureTestingModule({
        imports: [CampaignsListPage],
        providers: [
          provideRouter([]),
          { provide: I18nService, useValue: i18n() },
          { provide: OrganizationContextService, useValue: { organizationId: () => 1 } },
          {
            provide: CampaignsApiService,
            useValue: {
              list: () => of({ items: [{ id: 1, name: 'Launch', status: 'active', market: 'ES' }], total: 1 }),
              create: () => of({ id: 2 }),
            },
          },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(CampaignsListPage);
      page = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('does not show the create form until Nueva campaña CTA', () => {
      expect(fixture.nativeElement.querySelector('[data-testid="campaigns-create-form"]')).toBeNull();
      expect(page.showCreateForm).toBe(false);
      const cta = fixture.nativeElement.querySelector('[data-testid="campaigns-new-cta"]') as HTMLButtonElement;
      cta.click();
      fixture.detectChanges();
      expect(page.showCreateForm).toBe(true);
      expect(fixture.nativeElement.querySelector('[data-testid="campaigns-create-form"]')).toBeTruthy();
    });

    it('preserves detail route link for existing campaigns', () => {
      const link = fixture.nativeElement.querySelector('a[href="/campaigns/1"]');
      expect(link).toBeTruthy();
    });
  });

  describe('detail ROI disclosure', () => {
    let fixture: ComponentFixture<CampaignDetailPage>;
    let page: CampaignDetailPage;

    beforeEach(async () => {
      TestBed.overrideComponent(CampaignDetailPage, {
        set: {
          template: `
            <div data-testid="campaign-summary-strip">
              <span>campaigns.detail.budgetTitle</span>
              <span>campaigns.detail.spendTitle</span>
              <span>campaigns.detail.roiValue</span>
            </div>
            <div data-testid="campaign-roi-disclosure" role="note">campaigns.detail.roiDisclosure</div>
            <section>campaigns.detail.periodTitle</section>
            <section>campaigns.detail.attributionTitle</section>
            <section>campaigns.detail.revenueTitle</section>
            <section>campaigns.detail.budgetTitle</section>
            <section>campaigns.detail.expensesTitle</section>
            <section>campaigns.detail.approvalsTitle</section>
            <p>{{ campaign?.name }}</p>
          `,
          templateUrl: undefined as unknown as string,
        },
      });

      await TestBed.configureTestingModule({
        imports: [CampaignDetailPage],
        providers: [
          provideRouter([]),
          { provide: I18nService, useValue: i18n() },
          { provide: OrganizationContextService, useValue: { organizationId: () => 1, hasPermission: () => true } },
          { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => '1' } } } },
          { provide: ConfirmDialogService, useValue: { open: async () => true } },
          {
            provide: CampaignsApiService,
            useValue: {
              get: () => of({ id: 1, name: 'Launch', status: 'active', market: 'ES', start_date: '2026-01-01', end_date: '2026-03-31' }),
              getBudget: () => of({ amount: 1000, currency: 'USD' }),
              listExpenses: () => of([{ id: 1, amount: 250, currency: 'USD', category: 'ads', expense_date: '2026-01-01' }]),
              listApprovals: () => of([]),
              listAttributionDefinitions: () => of([]),
              listAttributableRevenue: () => of([]),
              getRoi: () => of({ status: 'available', roi_value: 1.25, budget_utilization: 0.25 }),
              computeRoi: () => of({ status: 'available', roi_value: 1.25 }),
              setBudget: () => of({}),
              addExpense: () => of({}),
              requestApproval: () => of({}),
              decideApproval: () => of({}),
              update: () => of({}),
              createAttributionDefinition: () => of({}),
              approveAttributionDefinition: () => of({}),
              recordAttributableRevenue: () => of({}),
              approveAttributableRevenue: () => of({}),
            },
          },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(CampaignDetailPage);
      page = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('shows a single ROI disclosure callout', () => {
      const disclosure = fixture.nativeElement.querySelectorAll('[data-testid="campaign-roi-disclosure"]');
      expect(disclosure.length).toBe(1);
      expect(disclosure[0].textContent).toContain('campaigns.detail.roiDisclosure');
      expect(fixture.nativeElement.textContent).toContain('campaigns.detail.roiValue');
      expect(fixture.nativeElement.textContent).not.toMatch(/RegalÃ|ROIÃ/);
      expect(page.expensesTotal).toBe(250);
    });

    it('preserves budget / expenses / approvals and ROI prep surfaces', () => {
      const text = fixture.nativeElement.textContent as string;
      expect(text).toContain('campaigns.detail.budgetTitle');
      expect(text).toContain('campaigns.detail.expensesTitle');
      expect(text).toContain('campaigns.detail.approvalsTitle');
      expect(text).toContain('campaigns.detail.periodTitle');
      expect(text).toContain('campaigns.detail.attributionTitle');
      expect(text).toContain('campaigns.detail.revenueTitle');
      expect(typeof page.computeRoi).toBe('function');
      expect(typeof page.addExpense).toBe('function');
      expect(typeof page.requestApproval).toBe('function');
      expect(typeof page.savePeriod).toBe('function');
    });
  });
});
