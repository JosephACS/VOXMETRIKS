import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Invoice, InvoiceItem } from '../models/billing.models';

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
  error: string | null = null;
  loading = false;
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = 'Select an organization context.';
      return;
    }
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.error = 'Invalid invoice id';
      return;
    }
    this.loading = true;
    this.api.getInvoice(this.orgId!, id).subscribe({
      next: (inv) => {
        this.invoice = inv;
        this.loading = false;
        this.api.getInvoiceItems(this.orgId!, id).subscribe({
          next: (items) => (this.items = items),
          error: () => (this.items = []),
        });
      },
      error: (e) => {
        this.error = e.error?.detail?.message ?? e.error?.message ?? 'Error loading invoice';
        this.loading = false;
      },
    });
  }
}
