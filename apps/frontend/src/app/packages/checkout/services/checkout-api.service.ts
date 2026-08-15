import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  CheckoutConfirmRequest,
  CheckoutSession,
  OrganizationCheckoutCreateRequest,
  PersonalCheckoutCreateRequest,
  SafePaymentMethodPayload,
} from '../models/checkout.models';

const API = environment.apiUrl;

/**
 * Personal + Organization checkout-session adapters (Spec 052).
 * Organization calls require X-Organization-Id.
 */
@Injectable({ providedIn: 'root' })
export class CheckoutApiService {
  private readonly http = inject(HttpClient);

  private orgHeaders(organizationId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(organizationId) });
  }

  // ── Personal ──────────────────────────────────────────────────────────────

  createPersonal(body: PersonalCheckoutCreateRequest): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(`${API}/personal/checkout-sessions`, body);
  }

  getPersonal(checkoutId: number): Observable<CheckoutSession> {
    return this.http.get<CheckoutSession>(`${API}/personal/checkout-sessions/${checkoutId}`);
  }

  attachPersonalPaymentMethod(
    checkoutId: number,
    body: SafePaymentMethodPayload,
  ): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(
      `${API}/personal/checkout-sessions/${checkoutId}/payment-method`,
      body,
    );
  }

  confirmPersonal(
    checkoutId: number,
    body: CheckoutConfirmRequest,
  ): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(
      `${API}/personal/checkout-sessions/${checkoutId}/confirm`,
      body,
    );
  }

  cancelPersonal(checkoutId: number): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(
      `${API}/personal/checkout-sessions/${checkoutId}/cancel`,
      {},
    );
  }

  // ── Organization ──────────────────────────────────────────────────────────

  createOrganization(
    organizationId: number,
    body: OrganizationCheckoutCreateRequest,
  ): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(`${API}/subscriptions/checkout-sessions`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  getOrganization(organizationId: number, checkoutId: number): Observable<CheckoutSession> {
    return this.http.get<CheckoutSession>(
      `${API}/subscriptions/checkout-sessions/${checkoutId}`,
      { headers: this.orgHeaders(organizationId) },
    );
  }

  attachOrganizationPaymentMethod(
    organizationId: number,
    checkoutId: number,
    body: SafePaymentMethodPayload,
  ): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(
      `${API}/subscriptions/checkout-sessions/${checkoutId}/payment-method`,
      body,
      { headers: this.orgHeaders(organizationId) },
    );
  }

  confirmOrganization(
    organizationId: number,
    checkoutId: number,
    body: CheckoutConfirmRequest,
  ): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(
      `${API}/subscriptions/checkout-sessions/${checkoutId}/confirm`,
      body,
      { headers: this.orgHeaders(organizationId) },
    );
  }

  cancelOrganization(organizationId: number, checkoutId: number): Observable<CheckoutSession> {
    return this.http.post<CheckoutSession>(
      `${API}/subscriptions/checkout-sessions/${checkoutId}/cancel`,
      {},
      { headers: this.orgHeaders(organizationId) },
    );
  }
}
