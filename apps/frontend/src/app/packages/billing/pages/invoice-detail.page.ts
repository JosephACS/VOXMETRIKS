import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Invoice, InvoiceItem, PaymentAttempt } from '../models/billing.models';

@Component({
  selector: 'app-invoice-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="invoice-detail-page">
      <a routerLink="/billing/invoices" class="back-link">← Invoices</a>
      @if (loading) {
        <p>Loading…</p>
      } @else if (error && !invoice) {
        <p class="error">{{ error }}</p>
      } @else if (!invoice) {
        <p class="empty-state">Invoice not found.</p>
      } @else {
        <div class="page-header">
          <h1>{{ invoice.invoice_number }}</h1>
          <span class="badge" [class]="'badge--' + invoice.status">{{ invoice.status }}</span>
        </div>
        @if (invoice.status === 'past_due') {
          <div class="alert alert--danger">
            Past due — settle outstanding balance to restore full subscription access.
          </div>
        }
        <dl class="meta">
          <dt>Currency</dt><dd>{{ invoice.currency || 'No disponible' }}</dd>
          <dt>Subtotal</dt><dd>{{ invoice.subtotal | number:'1.2-2' }}</dd>
          <dt>Total</dt><dd>{{ invoice.total | number:'1.2-2' }}</dd>
          <dt>Paid</dt><dd>{{ invoice.amount_paid | number:'1.2-2' }}</dd>
          <dt>Due</dt><dd>{{ invoice.amount_due | number:'1.2-2' }}</dd>
          <dt>Due date</dt>
          <dd>{{ invoice.due_date ? (invoice.due_date | date:'mediumDate') : 'No disponible' }}</dd>
          <dt>Issued</dt>
          <dd>{{ invoice.issued_at ? (invoice.issued_at | date:'short') : 'No disponible' }}</dd>
        </dl>

        <section class="dunning-panel">
          <h2>Dunning / mora</h2>
          @if (dunning) {
            <dl class="meta">
              <dt>Estado</dt><dd>{{ dunning.status }}</dd>
              <dt>Reintentos</dt><dd>{{ dunning.retry_count }}</dd>
              <dt>Próximo reintento</dt>
              <dd>{{ dunning.next_retry_at ? (dunning.next_retry_at | date:'short') : 'No disponible' }}</dd>
              <dt>Gracia hasta</dt>
              <dd>{{ dunning.grace_until ? (dunning.grace_until | date:'short') : 'No disponible' }}</dd>
              <dt>Último error</dt>
              <dd>{{ dunning.last_error_sanitized || 'No disponible' }}</dd>
            </dl>
            @if (dunning.status === 'grace' || dunning.status === 'limited') {
              <button type="button" class="btn btn--secondary" [disabled]="busy"
                (click)="expireGrace()">Expirar gracia (mock → blocked)</button>
            }
          } @else {
            <p class="muted">Sin registro de mora para esta factura.</p>
          }
        </section>

        <h2>Payment attempts</h2>
        @if (attempts.length) {
          <table class="data-table">
            <thead>
              <tr><th>ID</th><th>Amount</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              @for (a of attempts; track a.id) {
                <tr>
                  <td>{{ a.id }} @if (a.is_mock) { <span class="badge badge--mock">[MOCK]</span> }</td>
                  <td>{{ a.amount | number:'1.2-2' }} {{ a.currency }}</td>
                  <td>{{ a.status }}</td>
                  <td class="actions">
                    @if (a.status === 'created' || a.status === 'processing') {
                      <button type="button" class="btn btn--danger" [disabled]="busy"
                        (click)="failAttempt(a.id)">Marcar fallido (mock)</button>
                      <button type="button" class="btn btn--primary" [disabled]="busy"
                        (click)="confirmAttempt(a.id)">Confirmar (mock)</button>
                    }
                    @if (a.status === 'failed') {
                      <button type="button" class="btn btn--secondary" [disabled]="busy"
                        (click)="retryAttempt(a.id)">Reintentar pago (mock)</button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        } @else {
          <p class="empty-state">No payment attempts.</p>
          @if (invoice.status === 'issued' || invoice.status === 'past_due' || invoice.status === 'partially_paid') {
            <button type="button" class="btn btn--primary" [disabled]="busy"
              (click)="createAttempt()">Crear intento mock</button>
          }
        }

        <h2>Line items</h2>
        @if (items.length) {
          <table class="data-table">
            <thead>
              <tr><th>Description</th><th>Qty</th><th>Unit</th><th>Amount</th></tr>
            </thead>
            <tbody>
              @for (it of items; track it.id) {
                <tr>
                  <td>{{ it.description || 'No disponible' }}</td>
                  <td>{{ it.quantity }}</td>
                  <td>{{ it.unit_price | number:'1.2-2' }}</td>
                  <td>{{ it.amount | number:'1.2-2' }}</td>
                </tr>
              }
            </tbody>
          </table>
        } @else {
          <p class="empty-state">No line items.</p>
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

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = 'Select an organization context.';
      return;
    }
    this.invoiceId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.invoiceId) {
      this.error = 'Invalid invoice id';
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
        this.error = e.error?.detail?.message ?? e.error?.message ?? 'Error loading invoice';
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
      next: () => { this.busy = false; this.info = 'Intento mock creado'; this.reload(); },
      error: (e) => {
        this.busy = false;
        this.error = e.error?.detail?.message ?? 'No se pudo crear el intento';
      },
    });
  }

  failAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.failPaymentAttempt(this.orgId, id, 'mock_card_declined').subscribe({
      next: () => { this.busy = false; this.info = 'Intento fallido → dunning abierto'; this.reload(); },
      error: (e) => {
        this.busy = false;
        this.error = e.error?.detail?.message ?? 'Fail falló';
      },
    });
  }

  confirmAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.confirmMockAttempt(this.orgId, id).subscribe({
      next: () => { this.busy = false; this.info = 'Pago mock confirmado'; this.reload(); },
      error: (e) => {
        this.busy = false;
        this.error = e.error?.detail?.message ?? 'Confirm falló';
      },
    });
  }

  retryAttempt(id: number): void {
    if (!this.orgId) return;
    this.busy = true;
    this.api.retryPaymentAttempt(this.orgId, id, `retry-${id}-${Date.now()}`).subscribe({
      next: () => { this.busy = false; this.info = 'Reintento mock creado'; this.reload(); },
      error: (e) => {
        this.busy = false;
        this.error = e.error?.detail?.message ?? 'Retry falló (¿doble concurrente?)';
      },
    });
  }

  expireGrace(): void {
    if (!this.orgId || !this.dunning) return;
    this.busy = true;
    this.api.expireDunningGrace(this.orgId, this.dunning.id).subscribe({
      next: () => { this.busy = false; this.info = 'Gracia expirada → acceso blocked'; this.reload(); },
      error: (e) => {
        this.busy = false;
        this.error = e.error?.detail?.message ?? 'Expire grace falló';
      },
    });
  }
}
