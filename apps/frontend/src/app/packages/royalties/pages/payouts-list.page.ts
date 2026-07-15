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
        <div class="alert alert--warn" role="status">
          {{ 'royalties.payout.simulatedBanner' | t:lang() }}
        </div>

        <app-enterprise-page-header
          [title]="'royalties.payouts.title' | t:lang()"
          [subtitle]="'royalties.term.simulatedPayout.help' | t:lang()"
        />

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

        <app-enterprise-empty-state
          [title]="'royalties.payouts.empty' | t:lang()"
          [description]="'royalties.payouts.emptyBody' | t:lang()"
        />
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
