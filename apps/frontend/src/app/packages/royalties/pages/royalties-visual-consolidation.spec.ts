import { Component, Input } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { RoyaltiesDashboardPage } from './royalties-dashboard.page';
import { PayoutsListPage } from './payouts-list.page';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { AuthService } from '../../../core/services/auth.service';
import { LocaleFormatService } from '../../../core/services/locale-format.service';
import { UiPreferencesService } from '../../../core/services/ui-preferences.service';
import {
  EnterpriseFormFieldComponent,
  EnterprisePageHeaderComponent,
  EnterpriseSectionCardComponent,
} from '../../../shared/components/enterprise';

const METRICS = {
  distributable_pool_approved: 100,
  distributable_pool_allocated_or_closed: 40,
  pool_count: 2,
  settlement_gross_total: 90,
  settlement_net_total: 80,
  settlement_count: 1,
  payout_paid_simulated_total: 20,
  payout_batch_count: 1,
  simulated_only: true,
  income_note: 'note',
};

/**
 * Vitest JIT fails to bind parent pipes into enterprise `input()` signals (NG0950/NG0303).
 * Page templates stay productive; leaf shells use classic @Input so audited markup is still exercised.
 */
@Component({
  selector: 'app-enterprise-page-header',
  standalone: true,
  template: `
    <header>
      <h1>{{ title }}</h1>
      @if (subtitle) {
        <p>{{ subtitle }}</p>
      }
      <ng-content />
    </header>
  `,
})
class EnterprisePageHeaderStub {
  @Input({ required: true }) title!: string;
  @Input() subtitle?: string;
}

@Component({
  selector: 'app-enterprise-form-field',
  standalone: true,
  template: `
    <label>
      <span>{{ label }}</span>
      <ng-content />
    </label>
  `,
})
class EnterpriseFormFieldStub {
  @Input({ required: true }) label!: string;
  @Input() required = false;
}

@Component({
  selector: 'app-enterprise-section-card',
  standalone: true,
  template: `
    <section>
      @if (title) {
        <h2>{{ title }}</h2>
      }
      <ng-content />
    </section>
  `,
})
class EnterpriseSectionCardStub {
  @Input() title?: string;
}

async function configureDashboard(opts: { canPayout: boolean; canView: boolean }) {
  TestBed.resetTestingModule();
  TestBed.overrideComponent(RoyaltiesDashboardPage, {
    remove: { imports: [EnterprisePageHeaderComponent, EnterpriseSectionCardComponent] },
    add: { imports: [EnterprisePageHeaderStub, EnterpriseSectionCardStub] },
  });
  await TestBed.configureTestingModule({
    imports: [RoyaltiesDashboardPage],
    providers: [
      provideRouter([]),
      UiPreferencesService,
      I18nService,
      LocaleFormatService,
      {
        provide: OrganizationContextService,
        useValue: {
          organizationId: () => 1,
          hasPermission: (code: string) => {
            if (code === 'royalty.payout') return opts.canPayout;
            if (code === 'royalty.view') return opts.canView;
            return false;
          },
        },
      },
      {
        provide: AuthService,
        useValue: { getUser: () => ({ username: 'ops', preferences: {} }) },
      },
      {
        provide: RoyaltiesApiService,
        useValue: { getMetrics: () => of(METRICS) },
      },
    ],
  }).compileComponents();
}

function payoutLinks(root: HTMLElement): HTMLAnchorElement[] {
  return Array.from(root.querySelectorAll('a[href="/payouts"]')) as HTMLAnchorElement[];
}

describe('Royalties visual consolidation', () => {
  it('uses expandable glossary and places quick access before metrics', async () => {
    await configureDashboard({ canPayout: false, canView: true });
    const fixture = TestBed.createComponent(RoyaltiesDashboardPage);
    fixture.detectChanges();
    const root = fixture.nativeElement as HTMLElement;
    const glossary = root.querySelector('[data-testid="royalties-glossary"]') as HTMLDetailsElement;
    expect(glossary).toBeTruthy();
    expect(glossary.open).toBe(false);
    const access = root.querySelector('[data-testid="royalties-quick-access"]');
    expect(access).toBeTruthy();
    expect(access!.compareDocumentPosition(glossary) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('with royalty.payout shows exactly one primary /payouts link', async () => {
    await configureDashboard({ canPayout: true, canView: true });
    const fixture = TestBed.createComponent(RoyaltiesDashboardPage);
    fixture.detectChanges();
    const root = fixture.nativeElement as HTMLElement;
    const links = payoutLinks(root);
    expect(links.length).toBe(1);
    expect(links[0].classList.contains('btn--primary')).toBe(true);
    expect(links[0].textContent).toContain('Pagos simulados');
    expect(root.querySelector('[data-testid="royalties-payouts-link"]')).toBe(links[0]);
    expect(root.textContent).toContain('Resumen de regalías');
    expect(root.textContent).toContain('Liquidaciones');
    expect(root.textContent).not.toMatch(/RegalÃ|liquidaciÃ/);
  });

  it('without royalty.payout but with royalty.view shows exactly one secondary /payouts link', async () => {
    await configureDashboard({ canPayout: false, canView: true });
    const fixture = TestBed.createComponent(RoyaltiesDashboardPage);
    fixture.detectChanges();
    const root = fixture.nativeElement as HTMLElement;
    const links = payoutLinks(root);
    expect(links.length).toBe(1);
    expect(links[0].classList.contains('btn--secondary')).toBe(true);
    expect(links[0].classList.contains('btn--primary')).toBe(false);
    expect(links[0].textContent).toContain('Pagos simulados');
  });

  it('labels payouts list honestly: open by ID, settlements link, no empty-batch claim', async () => {
    TestBed.resetTestingModule();
    TestBed.overrideComponent(PayoutsListPage, {
      remove: {
        imports: [
          EnterprisePageHeaderComponent,
          EnterpriseFormFieldComponent,
          EnterpriseSectionCardComponent,
        ],
      },
      add: {
        imports: [EnterprisePageHeaderStub, EnterpriseFormFieldStub, EnterpriseSectionCardStub],
      },
    });
    await TestBed.configureTestingModule({
      imports: [PayoutsListPage],
      providers: [
        provideRouter([]),
        UiPreferencesService,
        I18nService,
        LocaleFormatService,
        { provide: OrganizationContextService, useValue: { organizationId: () => 1 } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(PayoutsListPage);
    fixture.detectChanges();
    const root = fixture.nativeElement as HTMLElement;
    const text = root.textContent || '';

    expect(root.querySelector('[data-testid="payouts-sim-banner"]')).toBeTruthy();
    expect(text).toContain('Pagos simulados');
    expect(text).toContain('Académico');
    expect(text).toContain(
      'Esta versión no ofrece un listado de lotes. Abre uno por su ID o créalo desde una liquidación finalizada.',
    );
    expect(root.querySelector('[data-testid="payouts-no-list-help"]')).toBeTruthy();
    expect(root.querySelector('[data-testid="payouts-settlements-link"]')).toBeTruthy();
    expect(root.querySelector('a[href="/royalties/settlements"]')).toBeTruthy();
    expect(text).toContain('Abrir lote por ID');
    expect(text).toContain('Liquidaciones');
    expect(text).not.toContain('Aún no hay lotes de pago');
    expect(text).not.toContain('No payout batches yet');
    expect(text).not.toMatch(/RegalÃ|Pagos de regalÃ|liquidaciÃ/);
  });
});
