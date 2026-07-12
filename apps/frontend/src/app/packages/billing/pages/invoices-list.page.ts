import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Invoice } from '../models/billing.models';

@Component({
  selector: 'app-invoices-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="invoices-list-page">
      @if (hasPastDue) {
        <div class="alert alert--danger">
          ⚠️ You have past-due invoices. Please settle outstanding payments to restore full access.
        </div>
      }
      <div class="page-header">
        <h1>Invoices</h1>
        <a routerLink="/billing/payment-attempts" class="btn btn--secondary">Payment attempts</a>
      </div>
      <div class="filter-bar">
        <select (change)="onStatusFilter($event)" class="select">
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="issued">Issued</option>
          <option value="partially_paid">Partially Paid</option>
          <option value="paid">Paid</option>
          <option value="past_due">Past Due</option>
          <option value="void">Void</option>
          <option value="credited">Credited</option>
        </select>
      </div>
      @if (loading) {
        <p>Loading…</p>
      } @else if (invoices.length) {
        <table class="data-table">
          <thead>
            <tr>
              <th>Number</th><th>Status</th><th>Total</th><th>Paid</th><th>Due</th><th>Issued</th>
            </tr>
          </thead>
          <tbody>
            @for (inv of invoices; track inv.id) {
              <tr>
                <td><a [routerLink]="['/billing/invoices', inv.id]">{{ inv.invoice_number }}</a></td>
                <td><span class="badge" [class]="'badge--' + inv.status">{{ inv.status }}</span></td>
                <td>{{ inv.total | number:'1.2-2' }} {{ inv.currency }}</td>
                <td>{{ inv.amount_paid | number:'1.2-2' }}</td>
                <td>{{ inv.amount_due | number:'1.2-2' }}</td>
                <td>{{ inv.issued_at | date:'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else if (!error) {
        <p class="empty-state">No invoices found. Use the demo seed or billing API to create synthetic invoices.</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class InvoicesListPage implements OnInit {
  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  invoices: Invoice[] = [];
  hasPastDue = false;
  error: string | null = null;
  statusFilter = '';
  orgId: number | null = null;
  loading = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = 'Select an organization context.';
      return;
    }
    this.loadInvoices();
  }

  loadInvoices(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;
    this.api.listInvoices(this.orgId!, { status: this.statusFilter || undefined }).subscribe({
      next: (res) => {
        this.invoices = res.items;
        this.hasPastDue = res.items.some((i) => i.status === 'past_due');
        this.loading = false;
      },
      error: (e) => {
        this.error = e.error?.detail?.message ?? e.error?.message ?? 'Error loading invoices';
        this.loading = false;
      },
    });
  }

  onStatusFilter(event: Event): void {
    this.statusFilter = (event.target as HTMLSelectElement).value;
    this.loadInvoices();
  }
}
