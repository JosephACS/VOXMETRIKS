import { describe, expect, it } from 'vitest';
import {
  isCreditNoteInvoice,
  isManualTransferInvoice,
  isRefundablePayment,
} from './billing-option-filters';

describe('billing option filters', () => {
  it('refunds: allows refundable statuses and excludes reversed/refunded', () => {
    expect(isRefundablePayment({ status: 'recorded' })).toBe(true);
    expect(isRefundablePayment({ status: 'settled' })).toBe(true);
    expect(isRefundablePayment({ status: 'reconciled' })).toBe(true);
    expect(isRefundablePayment({ status: 'partially_refunded' })).toBe(true);
    expect(isRefundablePayment({ status: 'refunded' })).toBe(false);
    expect(isRefundablePayment({ status: 'reversed' })).toBe(false);
    expect(isRefundablePayment({ status: 'succeeded' })).toBe(false);
    expect(isRefundablePayment({ status: 'paid' })).toBe(false);
    expect(isRefundablePayment({ status: 'failed' })).toBe(false);
  });

  it('manual transfer: requires amount_due > 0 and excludes void/paid/credited', () => {
    expect(isManualTransferInvoice({ status: 'issued', amount_due: 10 })).toBe(true);
    expect(isManualTransferInvoice({ status: 'partially_paid', amount_due: 1 })).toBe(true);
    expect(isManualTransferInvoice({ status: 'issued', amount_due: 0 })).toBe(false);
    expect(isManualTransferInvoice({ status: 'void', amount_due: 50 })).toBe(false);
    expect(isManualTransferInvoice({ status: 'paid', amount_due: 50 })).toBe(false);
    expect(isManualTransferInvoice({ status: 'credited', amount_due: 50 })).toBe(false);
  });

  it('credit notes: excludes void and draft; keeps issued/paid/etc.', () => {
    expect(isCreditNoteInvoice({ status: 'issued' })).toBe(true);
    expect(isCreditNoteInvoice({ status: 'paid' })).toBe(true);
    expect(isCreditNoteInvoice({ status: 'partially_paid' })).toBe(true);
    expect(isCreditNoteInvoice({ status: 'void' })).toBe(false);
    expect(isCreditNoteInvoice({ status: 'draft' })).toBe(false);
  });
});
