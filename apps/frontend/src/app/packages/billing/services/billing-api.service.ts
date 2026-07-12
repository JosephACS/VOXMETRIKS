import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  BillingProfile,
  CreditNote,
  Invoice,
  InvoiceItem,
  LedgerEntry,
  PaginatedResponse,
  Payment,
  PaymentAttempt,
  Refund,
} from '../models/billing.models';

const BASE = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class BillingApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(orgId) });
  }

  // ── Profile ──────────────────────────────────────────────────────────────

  getProfile(orgId: number): Observable<BillingProfile> {
    return this.http.get<BillingProfile>(`${BASE}/billing/profile`, {
      headers: this.orgHeaders(orgId),
    });
  }

  createProfile(orgId: number, body: Partial<BillingProfile>): Observable<BillingProfile> {
    return this.http.post<BillingProfile>(`${BASE}/billing/profile`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  updateProfile(orgId: number, body: Partial<BillingProfile>): Observable<BillingProfile> {
    return this.http.patch<BillingProfile>(`${BASE}/billing/profile`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Invoices ─────────────────────────────────────────────────────────────

  listInvoices(
    orgId: number,
    params?: { status?: string; page?: number; page_size?: number },
  ): Observable<PaginatedResponse<Invoice>> {
    let p = new HttpParams();
    if (params?.status) p = p.set('status', params.status);
    if (params?.page) p = p.set('page', String(params.page));
    if (params?.page_size) p = p.set('page_size', String(params.page_size));
    return this.http.get<PaginatedResponse<Invoice>>(`${BASE}/billing/invoices`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  createInvoice(orgId: number, body: object): Observable<Invoice> {
    return this.http.post<Invoice>(`${BASE}/billing/invoices`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  getInvoice(orgId: number, id: number): Observable<Invoice> {
    return this.http.get<Invoice>(`${BASE}/billing/invoices/${id}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  getInvoiceItems(orgId: number, invoiceId: number): Observable<InvoiceItem[]> {
    return this.http.get<InvoiceItem[]>(`${BASE}/billing/invoices/${invoiceId}/items`, {
      headers: this.orgHeaders(orgId),
    });
  }

  issueInvoice(orgId: number, id: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${BASE}/billing/invoices/${id}/issue`, {}, {
      headers: this.orgHeaders(orgId),
    });
  }

  voidInvoice(orgId: number, id: number, reason?: string): Observable<Invoice> {
    return this.http.post<Invoice>(`${BASE}/billing/invoices/${id}/void`, { reason }, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Payment Attempts ──────────────────────────────────────────────────────

  listPaymentAttempts(
    orgId: number,
    params?: { invoice_id?: number; page?: number; page_size?: number },
  ): Observable<PaginatedResponse<PaymentAttempt>> {
    let p = new HttpParams();
    if (params?.invoice_id) p = p.set('invoice_id', String(params.invoice_id));
    if (params?.page) p = p.set('page', String(params.page));
    return this.http.get<PaginatedResponse<PaymentAttempt>>(`${BASE}/billing/payment-attempts`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  createPaymentAttempt(orgId: number, body: object): Observable<PaymentAttempt> {
    return this.http.post<PaymentAttempt>(`${BASE}/billing/payment-attempts`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  confirmMockAttempt(orgId: number, id: number): Observable<PaymentAttempt> {
    return this.http.post<PaymentAttempt>(`${BASE}/billing/payment-attempts/${id}/confirm`, {}, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Payments ──────────────────────────────────────────────────────────────

  listPayments(
    orgId: number,
    params?: { page?: number; page_size?: number },
  ): Observable<PaginatedResponse<Payment>> {
    let p = new HttpParams();
    if (params?.page) p = p.set('page', String(params.page));
    return this.http.get<PaginatedResponse<Payment>>(`${BASE}/billing/payments`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  settlePayment(orgId: number, id: number): Observable<Payment> {
    return this.http.post<Payment>(`${BASE}/billing/payments/${id}/settle`, {}, {
      headers: this.orgHeaders(orgId),
    });
  }

  reconcilePayment(orgId: number, id: number): Observable<Payment> {
    return this.http.post<Payment>(`${BASE}/billing/payments/${id}/reconcile`, {}, {
      headers: this.orgHeaders(orgId),
    });
  }

  createManualTransfer(orgId: number, body: object): Observable<Payment> {
    return this.http.post<Payment>(`${BASE}/billing/manual-transfer`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Refunds ───────────────────────────────────────────────────────────────

  listRefunds(orgId: number): Observable<PaginatedResponse<Refund>> {
    return this.http.get<PaginatedResponse<Refund>>(`${BASE}/billing/refunds`, {
      headers: this.orgHeaders(orgId),
    });
  }

  createRefund(orgId: number, body: object): Observable<Refund> {
    return this.http.post<Refund>(`${BASE}/billing/refunds`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Credit Notes ──────────────────────────────────────────────────────────

  listCreditNotes(orgId: number): Observable<PaginatedResponse<CreditNote>> {
    return this.http.get<PaginatedResponse<CreditNote>>(`${BASE}/billing/credit-notes`, {
      headers: this.orgHeaders(orgId),
    });
  }

  createCreditNote(orgId: number, body: object): Observable<CreditNote> {
    return this.http.post<CreditNote>(`${BASE}/billing/credit-notes`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  applyCreditNote(orgId: number, id: number): Observable<CreditNote> {
    return this.http.post<CreditNote>(`${BASE}/billing/credit-notes/${id}/apply`, {}, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Ledger ────────────────────────────────────────────────────────────────

  getLedger(
    orgId: number,
    params?: { entry_type?: string; page?: number; page_size?: number },
  ): Observable<PaginatedResponse<LedgerEntry>> {
    let p = new HttpParams();
    if (params?.entry_type) p = p.set('entry_type', params.entry_type);
    if (params?.page) p = p.set('page', String(params.page));
    return this.http.get<PaginatedResponse<LedgerEntry>>(`${BASE}/billing/ledger`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }
}
