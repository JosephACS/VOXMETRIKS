/** Presentation filters for billing option selectors (aligned with backend contracts). */

export interface Statused {
  status?: string | null;
}

export interface DueInvoice extends Statused {
  amount_due?: number | null;
}

/** Payments that may still be refunded; remaining balance is enforced by the API. */
export function isRefundablePayment(p: Statused): boolean {
  const status = String(p.status || '').toLowerCase();
  if (!status) return false;
  if (status === 'reversed' || status === 'refunded') return false;
  return ['recorded', 'settled', 'reconciled', 'partially_refunded'].includes(status);
}

/** Invoices eligible for a manual transfer: due balance and not closed-out. */
export function isManualTransferInvoice(inv: DueInvoice): boolean {
  const status = String(inv.status || '').toLowerCase();
  if (status === 'void' || status === 'paid' || status === 'credited') return false;
  return Number(inv.amount_due) > 0;
}

/** Invoices that can receive a credit note (not draft/void). */
export function isCreditNoteInvoice(inv: Statused): boolean {
  const status = String(inv.status || '').toLowerCase();
  if (!status) return false;
  return status !== 'void' && status !== 'draft';
}
