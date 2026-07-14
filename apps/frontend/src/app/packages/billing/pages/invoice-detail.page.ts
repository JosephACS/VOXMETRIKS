import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Invoice, InvoiceItem, PaymentAttempt } from '../models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';

@Component({
  selector: 'app-invoice-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TranslatePipe,
    StatusLabelPipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
  ],
  template: `
    <div class="vx-enterprise invoice-detail-page">
      <a routerLink="/billing/invoices" class="back-link">{{ 'billing.invoiceDetail.back' | t:lang() }}</a>
      @if (loading) {
        <p>{{ 'billing.invoiceDetail.loading' | t:lang() }}</p>
      } @else if (error && !invoice) {
        <p class="error">{{ error }}</p>
      } @else if (!invoice) {
        <p class="empty-state">{{ 'billing.invoiceDetail.notFound' | t:lang() }}</p>
      } @else {
        <div class="page-header">
          <h1>{{ invoice.invoice_number }}</h1>
          <span class="badge" [class]="'badge--' + invoice.status">{{ invoice.status | statusLabel }}</span>
        </div>
        @if (invoice.status === 'past_due') {
          <div class="alert alert--danger">
            {{ 'billing.invoiceDetail.pastDueAlert' | t:lang() }}
          </div>
        }
        <dl class="meta">
          <dt>{{ 'common.currency' | t:lang() }}</dt>
          <dd>{{ invoice.currency || ('common.notAvailable' | t:lang()) }}</dd>
          <dt>{{ 'billing.invoiceDetail.subtotal' | t:lang() }}</dt>
          <dd>{{ invoice.subtotal | localeMoney:invoice.currency }}</dd>
          <dt>{{ 'billing.invoiceDetail.total' | t:lang() }}</dt>
          <dd>{{ invoice.total | localeMoney:invoice.currency }}</dd>
          <dt>{{ 'billing.invoiceDetail.paid' | t:lang() }}</dt>
          <dd>{{ invoice.amount_paid | localeMoney:invoice.currency }}</dd>
          <dt>{{ 'billing.invoiceDetail.due' | t:lang() }}</dt>
          <dd>{{ invoice.amount_due | localeMoney:invoice.currency }}</dd>
          <dt>{{ 'billing.invoiceDetail.dueDate' | t:lang() }}</dt>
          <dd>{{ invoice.due_date | localeDate }}</dd>
          <dt>{{ 'billing.invoiceDetail.issued' | t:lang() }}</dt>
          <dd>{{ invoice.issued_at | localeDate:true }}</dd>
        </dl>

        <section class="dunning-panel">
          <h2>{{ 'billing.invoiceDetail.dunning' | t:lang() }}</h2>
          @if (dunning) {
            <dl class="meta">
              <dt>{{ 'common.status' | t:lang() }}</dt>
              <dd>{{ dunning.status | statusLabel }}</dd>
              <dt>{{ 'billing.invoiceDetail.retries' | t:lang() }}</dt>
              <dd>{{ dunning.retry_count }}</dd>
              <dt>{{ 'billing.invoiceDetail.nextRetry' | t:lang() }}</dt>
              <dd>{{ dunning.next_retry_at | localeDate:true }}</dd>
              <dt>{{ 'billing.invoiceDetail.graceUntil' | t:lang() }}</dt>
              <dd>{{ dunning.grace_until | localeDate:true }}</dd>
              <dt>{{ 'billing.invoiceDetail.lastError' | t:lang() }}</dt>
              <dd>{{ dunning.last_error_sanitized || ('common.notAvailable' | t:lang()) }}</dd>
            </dl>
            @if (dunning.status === 'grace' || dunning.status === 'limited') {
              <button type="button" class="btn btn--secondary" [disabled]="busy"
                (click)="expireGrace()">{{ 'billing.invoiceDetail.expireGrace' | t:lang() }}</button>
            }
          } @else {
            <p class="muted">{{ 'billing.invoiceDetail.noDunning' | t:lang() }}</p>
          }
        </section>

        <h2>
          {{ 'billing.invoiceDetail.attempts' | t:lang() }}
          <span class="badge badge--mock">{{ 'billing.invoiceDetail.mockBadge' | t:lang() }}</span>
        </h2>
        <p class="muted">{{ 'billing.invoiceDetail.mockHint' | t:lang() }}</p>
        @if (attempts.length) {
          <div class="simulate-bar">
            <label for="mock-scenario">{{ 'billing.invoiceDetail.mockResult' | t:lang() }}</label>
            <select id="mock-scenario" [(ngModel)]="selectedScenario">
              @for (s of mockScenarios; track s) {
                <option [value]="s">{{ s }}</option>
              }
            </select>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'common.id' | t:lang() }}</th>
                <th>{{ 'common.amount' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th>{{ 'common.actions' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (a of attempts; track a.id) {
                <tr>
                  <td>{{ a.id }} @if (a.is_mock) { <span class="badge badge--mock">[{{ 'common.mock' | t:lang() }}]</span> }</td>
                  <td>{{ a.amount | localeMoney:a.currency }}</td>
                  <td>
                    <span [class.ok]="a.status === 'succeeded'"
                          [class.err]="a.status === 'failed'"
                          [class.warn]="a.status === 'processing'">
                      {{ a.status | statusLabel }}
                    </span>
                  </td>
                  <td class="actions">
                    @if (a.status === 'created' || a.status === 'processing') {
                      <button type="button" class="btn btn--danger" [disabled]="busy"
                        (click)="failAttempt(a.id)">{{ 'billing.invoiceDetail.markFailed' | t:lang() }}</button>
                      <button type="button" class="btn btn--primary" [disabled]="busy"
                        (click)="confirmAttempt(a.id)">{{ 'billing.invoiceDetail.confirmMock' | t:lang() }}</button>
                      <button type="button" class="btn btn--secondary" [disabled]="busy"
                        (click)="simulateAttempt(a.id)">{{ 'billing.invoiceDetail.simulateResult' | t:lang() }}</button>
                    }
                    @if (a.status === 'failed') {
                      <button type="button" class="btn btn--secondary" [disabled]="busy"
                        (click)="retryAttempt(a.id)">{{ 'billing.invoiceDetail.retryMock' | t:lang() }}</button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        } @else {
          <p class="empty-state">{{ 'billing.invoiceDetail.noAttempts' | t:lang() }}</p>
          @if (invoice.status === 'issued' || invoice.status === 'past_due' || invoice.status === 'partially_paid') {
            <button type="button" class="btn btn--primary" [disabled]="busy"
              (click)="createAttempt()">{{ 'billing.invoiceDetail.createAttempt' | t:lang() }}</button>
          }
        }

        <h2>{{ 'billing.invoiceDetail.lineItems' | t:lang() }}</h2>
        @if (items.length) {
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'billing.invoiceDetail.description' | t:lang() }}</th>
                <th>{{ 'billing.invoiceDetail.qty' | t:lang() }}</th>
                <th>{{ 'billing.invoiceDetail.unit' | t:lang() }}</th>
                <th>{{ 'common.amount' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (it of items; track it.id) {
                <tr>
                  <td>{{ it.description || ('common.notAvailable' | t:lang()) }}</td>
                  <td>{{ it.quantity }}</td>
                  <td>{{ it.unit_price | localeMoney:invoice.currency }}</td>
                  <td>{{ it.amount | localeMoney:invoice.currency }}</td>
                </tr>
              }
            </tbody>
          </table>
        } @else {
          <p class="empty-state">{{ 'billing.invoiceDetail.noLines' | t:lang() }}</p>
        }
        @if (error) {
          <p class="error">{{ error }}</p>
        }
        @if (info) {
          <p class="success">{{ info }}</p>
        }
      }
    </div>
  `,
})
export class InvoiceDetailPage implements OnInit {
  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  invoice: Invoice | null = null;
  items: InvoiceItem[] = [];
  attempts: PaymentAttempt[] = [];
  dunning: {
    id: number;
    status: string;
    retry_count: number;
    next_retry_at?: string | null;
    grace_until?: string | null;
    last_error_sanitized?: string | null;
  } | null = null;
  error: string | null = null;
  info: string | null = null;
  loading = false;
  busy = false;
  orgId: number | null = null;
  invoiceId = 0;
  selectedScenario = 'succeeded';
  readonly mockScenarios = [
    'succeeded', 'declined', 'insufficient_funds', 'invalid_method', 'timeout',
    'processing', 'canceled', 'duplicate_event', 'partial_payment',
    'full_refund', 'partial_refund', 'reversal',
  ];

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.invoiceId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.invoiceId) {
      this.error = this.i18n.t('billing.invoiceDetail.invalidId');
      return;
    }
    this.reload();
  }

  reload(): void {
    if (!this.orgId || !this.invoiceId) return;
    this.loading = true;
    this.api.getInvoice(this.orgId, this.invoiceId).subscribe({
      next: (inv) => {
        this.invoice = inv;
        this.loading = false;
        this.api.getInvoiceItems(this.orgId!, this.invoiceId).subscribe({
          next: (items) => (this.items = items),
          error: () => (this.items = []),
        });
        this.api.listPaymentAttempts(this.orgId!, { invoice_id: this.invoiceId }).subscribe({
          next: (res) => (this.attempts = res.items || []),
          error: () => (this.attempts = []),
        });
        this.api.getDunningByInvoice(this.orgId!, this.invoiceId).subscribe({
          next: (d) => (this.dunning = d),
          error: () => (this.dunning = null),
        });
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e) || this.i18n.t('billing.invoiceDetail.loadError');
        this.loading = false;
      },
    });
  }

  createAttempt(): void {
    if (!this.orgId || !this.invoice) return;
    this.busy = true;
    this.error = null;
    this.api.createPaymentAttempt(this.orgId, {
      invoice_id: this.invoice.id,
      provider_code: 'academic_mock',
      idempotency_key: `inv-${this.invoice.id}-${Date.now()}`,
      amount: this.invoice.amount_due,
      currency: this.invoice.currency,
    }).subscribe({
      next: () => {
        this.busy = false;
        this.info = this.i18n.t('billing.invoiceDetail.attemptCreated');
        this.reload();
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  failAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.failPaymentAttempt(this.orgId, id, 'mock_card_declined').subscribe({
      next: () => {
        this.busy = false;
        this.info = this.i18n.t('billing.invoiceDetail.attemptFailed');
        this.reload();
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  confirmAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.confirmMockAttempt(this.orgId, id).subscribe({
      next: () => {
        this.busy = false;
        this.info = this.i18n.t('billing.invoiceDetail.paymentConfirmed');
        this.reload();
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  simulateAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.error = null;
    this.api.simulateMockAttempt(this.orgId, id, this.selectedScenario).subscribe({
      next: (res) => {
        this.busy = false;
        this.info = `[${this.i18n.t('billing.invoiceDetail.mockBadge')}] ${res.scenario}: ${res.message}`;
        this.reload();
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  retryAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.retryPaymentAttempt(this.orgId, id, `retry-${id}-${Date.now()}`).subscribe({
      next: () => {
        this.busy = false;
        this.info = this.i18n.t('billing.invoiceDetail.retryCreated');
        this.reload();
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  expireGrace(): void {
    if (!this.orgId || !this.dunning) return;
    this.busy = true;
    this.api.expireDunningGrace(this.orgId, this.dunning.id).subscribe({
      next: () => {
        this.busy = false;
        this.info = this.i18n.t('billing.invoiceDetail.graceExpired');
        this.reload();
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }
}
