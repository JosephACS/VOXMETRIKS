import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Invoice } from '../models/billing.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-invoices-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TranslatePipe,
    StatusLabelPipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise invoices-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        @if (hasPastDue) {
          <div class="alert alert--warn" role="status">
            {{ 'billing.invoiceDetail.pastDueAlert' | t:lang() }}
          </div>
        }

        <app-enterprise-page-header [title]="'billing.invoices.title' | t:lang()">
          <a routerLink="/billing/payment-attempts" class="btn btn--secondary">
            {{ 'billing.invoices.paymentAttempts' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'common.filter' | t:lang()">
          <div class="form-grid">
            <app-enterprise-form-field [label]="'common.status' | t:lang()">
              <select (change)="onStatusFilter($event)" class="select">
                <option value="">{{ 'billing.invoices.allStatuses' | t:lang() }}</option>
                <option value="draft">{{ 'draft' | statusLabel }}</option>
                <option value="issued">{{ 'issued' | statusLabel }}</option>
                <option value="partially_paid">{{ 'partially_paid' | statusLabel }}</option>
                <option value="paid">{{ 'paid' | statusLabel }}</option>
                <option value="past_due">{{ 'past_due' | statusLabel }}</option>
                <option value="void">{{ 'void' | statusLabel }}</option>
              </select>
            </app-enterprise-form-field>
          </div>
        </app-enterprise-section-card>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="loadInvoices()" />
        } @else if (!invoices.length) {
          <app-enterprise-empty-state
            [title]="'billing.invoices.empty' | t:lang()"
            [description]="'billing.invoices.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'billing.invoices.number' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'billing.invoices.total' | t:lang() }}</th>
                  <th>{{ 'billing.invoiceDetail.paid' | t:lang() }}</th>
                  <th>{{ 'billing.invoiceDetail.due' | t:lang() }}</th>
                  <th>{{ 'billing.invoiceDetail.issued' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (inv of invoices; track inv.id) {
                  <tr>
                    <td>
                      <a [routerLink]="['/billing/invoices', inv.id]">{{ inv.invoice_number }}</a>
                    </td>
                    <td><app-enterprise-status-badge [status]="inv.status" /></td>
                    <td>{{ inv.total | localeMoney:inv.currency }}</td>
                    <td>{{ inv.amount_paid | localeMoney:inv.currency }}</td>
                    <td>{{ inv.amount_due | localeMoney:inv.currency }}</td>
                    <td>{{ inv.issued_at | localeDate:true }}</td>
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
export class InvoicesListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  invoices: Invoice[] = [];
  hasPastDue = false;
  error: string | null = null;
  statusFilter = '';
  orgId: number | null = null;
  loading = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.loadInvoices();
  }

  loadInvoices(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;
    this.api.listInvoices(this.orgId, { status: this.statusFilter || undefined }).subscribe({
      next: (res) => {
        this.invoices = res.items;
        this.hasPastDue = res.items.some((i) => i.status === 'past_due');
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }

  onStatusFilter(event: Event): void {
    this.statusFilter = (event.target as HTMLSelectElement).value;
    this.loadInvoices();
  }
}
