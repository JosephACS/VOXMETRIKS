import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

/** No list-batches endpoint — entry by ID or after creating from a settlement. */
@Component({
  selector: 'app-payouts-list',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise payouts-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <div class="vx-sim-callout" role="status" data-testid="payouts-sim-banner">
          <span class="vx-sim-badge">{{ 'royalties.payouts.academicBadge' | t:lang() }}</span>
          <span>{{ 'royalties.payout.simulatedBanner' | t:lang() }}</span>
        </div>

        <app-enterprise-page-header
          [title]="'royalties.payouts.pageTitle' | t:lang()"
          [subtitle]="'royalties.payouts.pageSubtitle' | t:lang()"
        >
          <a
            routerLink="/royalties/settlements"
            class="btn btn--secondary"
            data-testid="payouts-settlements-link"
          >
            {{ 'royalties.nav.settlements' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        <p class="muted" data-testid="payouts-no-list-help">
          {{ 'royalties.payouts.noListHelp' | t:lang() }}
        </p>

        <app-enterprise-section-card [title]="'royalties.payouts.openById' | t:lang()">
          <div class="form-grid">
            <app-enterprise-form-field [label]="'royalties.payouts.batchId' | t:lang()">
              <input class="input" type="number" [(ngModel)]="batchIdInput" min="1" />
            </app-enterprise-form-field>
          </div>
          <button type="button" class="btn btn--primary" [disabled]="!batchIdInput" (click)="open()">
            {{ 'common.view' | t:lang() }}
          </button>
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class PayoutsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private orgCtx = inject(OrganizationContextService);
  private router = inject(Router);

  orgId: number | null = null;
  batchIdInput: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
  }

  open(): void {
    if (!this.batchIdInput) return;
    void this.router.navigate(['/payouts', this.batchIdInput]);
  }
}
