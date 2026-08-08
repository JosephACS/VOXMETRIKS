/** Billing domain models — Spec 019. */

export interface BillingProfile {
  id: number;
  organization_id: number;
  default_currency: string;
  legal_name: string | null;
  tax_id: string | null;
  billing_address: string | null;
  email: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Invoice {
  id: number;
  organization_id: number;
  billing_profile_id: number;
  subscription_id: number | null;
  invoice_number: string;
  currency: string;
  status: string;
  subtotal: number;
  total: number;
  amount_paid: number;
  amount_due: number;
  period_start: string | null;
  period_end: string | null;
  due_date: string | null;
  issued_at: string | null;
  paid_at: string | null;
  voided_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: number;
  invoice_id: number;
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
}

export interface PaymentAttempt {
  id: number;
  organization_id: number;
  invoice_id: number;
  provider_code: string;
  idempotency_key: string;
  amount: number;
  currency: string;
  status: string;
  provider_attempt_id: string | null;
  failure_reason: string | null;
  is_mock: boolean;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  organization_id: number;
  payment_attempt_id: number;
  provider_code: string;
  amount: number;
  currency: string;
  status: string;
  provider_payment_id: string | null;
  settled_at: string | null;
  reconciled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Refund {
  id: number;
  organization_id: number;
  payment_id: number;
  amount: number;
  currency: string;
  reason: string | null;
  status: string;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
  idempotency_key: string;
}

export interface CreateRefundRequest {
  payment_id: number | null;
  amount: number | null;
  reason: string | null;
  idempotency_key: string;
}

export interface CreditNote {
  id: number;
  organization_id: number;
  invoice_id: number;
  credit_note_number: string;
  amount: number;
  currency: string;
  reason: string | null;
  status: string;
  issued_at: string | null;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LedgerEntry {
  id: number;
  organization_id: number;
  entry_type: string;
  reference_type: string;
  reference_id: number;
  amount: number;
  currency: string;
  description: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
