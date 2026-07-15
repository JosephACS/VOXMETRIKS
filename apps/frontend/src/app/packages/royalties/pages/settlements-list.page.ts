import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { RoyaltySettlement } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-settlements-list',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, LocaleMoneyPipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise settlements-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'royalties.settlements.title' | t:lang()"
          [subtitle]="'royalties.term.settlement.help' | t:lang()"
        />

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!rows.length) {
          <app-enterprise-empty-state
            [title]="'royalties.settlements.empty' | t:lang()"
            [description]="'royalties.settlements.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'royalties.settlements.pool' | t:lang() }}</th>
                  <th>{{ 'royalties.settlements.gross' | t:lang() }}</th>
                  <th>{{ 'royalties.settlements.net' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (r of rows; track r.id) {
                  <tr>
                    <td>
                      <a [routerLink]="['/royalties/settlements', r.id]">#{{ r.id }}</a>
                    </td>
                    <td><app-enterprise-status-badge [status]="r.status" /></td>
                    <td>
                      <a [routerLink]="['/royalties/pools', r.pool_id]">#{{ r.pool_id }}</a>
                    </td>
                    <td>{{ r.gross_total | localeMoney:r.currency }}</td>
                    <td>{{ r.net_total | localeMoney:r.currency }}</td>
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
export class SettlementsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  rows: RoyaltySettlement[] = [];
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
    // Backend has no list-settlements; derive unique runs from statements.
    this.api.listStatements(this.orgId, { limit: 500 }).subscribe({
      next: (stmts) => {
        const ids = [...new Set(stmts.map((s) => s.settlement_run_id))];
        if (!ids.length) {
          this.rows = [];
          this.loading = false;
          return;
        }
        forkJoin(
          ids.map((id) =>
            this.api.getSettlement(this.orgId!, id).pipe(
              catchError(() => of(null)),
            ),
          ),
        )
          .pipe(map((list) => list.filter((x): x is RoyaltySettlement => !!x)))
          .subscribe({
            next: (runs) => {
              this.rows = runs.sort((a, b) => b.id - a.id);
              this.loading = false;
            },
            error: (e) => {
              this.error = userFacingHttpError(this.i18n, e);
              this.loading = false;
            },
          });
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }
}
