import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { RoyaltyStatement } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-statements-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TranslatePipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise statements-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'royalties.statements.title' | t:lang()"
          [subtitle]="'royalties.term.contractPct.help' | t:lang()"
        />

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!rows.length) {
          <app-enterprise-empty-state
            [title]="'royalties.statements.empty' | t:lang()"
            [description]="'royalties.statements.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'royalties.statements.settlement' | t:lang() }}</th>
                  <th>{{ 'royalties.settlements.net' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'royalties.pools.period' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (s of rows; track s.id) {
                  <tr>
                    <td>#{{ s.id }}</td>
                    <td>{{ s.party_name }}</td>
                    <td>
                      <a [routerLink]="['/royalties/settlements', s.settlement_run_id]">
                        #{{ s.settlement_run_id }}
                      </a>
                    </td>
                    <td>{{ s.net_amount | localeMoney:s.currency }}</td>
                    <td><app-enterprise-status-badge [status]="s.status" /></td>
                    <td>{{ s.period_start | localeDate }} — {{ s.period_end | localeDate }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      }
    </div>
  `,
})
export class StatementsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  rows: RoyaltyStatement[] = [];
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;
    this.api.listStatements(this.orgId).subscribe({
      next: (rows) => {
        this.rows = rows;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }
}
