import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { RoyaltyPool } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-pools-list',
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
    <div class="vx-enterprise pools-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'royalties.pools.title' | t:lang()"
          [subtitle]="'royalties.term.distributableIncome.help' | t:lang()"
        >
          <a routerLink="/royalties" class="btn btn--secondary">
            {{ 'royalties.nav.dashboard' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!pools.length) {
          <app-enterprise-empty-state
            [title]="'royalties.pools.empty' | t:lang()"
            [description]="'royalties.pools.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'royalties.pools.label' | t:lang() }}</th>
                  <th>{{ 'common.amount' | t:lang() }}</th>
                  <th>{{ 'royalties.pools.period' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (p of pools; track p.id) {
                  <tr>
                    <td>
                      <a [routerLink]="['/royalties/pools', p.id]">#{{ p.id }}</a>
                    </td>
                    <td><app-enterprise-status-badge [status]="p.status" /></td>
                    <td>{{ p.label || ('common.notAvailable' | t:lang()) }}</td>
                    <td>{{ p.total_amount | localeMoney:p.currency }}</td>
                    <td>{{ p.period_start | localeDate }} — {{ p.period_end | localeDate }}</td>
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
export class PoolsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  pools: RoyaltyPool[] = [];
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
    this.api.listPools(this.orgId).subscribe({
      next: (rows) => {
        this.pools = rows;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }
}
