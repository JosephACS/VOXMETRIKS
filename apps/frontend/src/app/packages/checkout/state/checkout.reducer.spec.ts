import { describe, expect, it } from 'vitest';
import { CheckoutSession } from '../models/checkout.models';
import {
  checkoutReducer,
  initialCheckoutState,
} from './checkout.reducer';

function session(overrides: Partial<CheckoutSession> = {}): CheckoutSession {
  return {
    id: 1,
    scope_type: 'personal',
    scope_id: 10,
    actor_user_id: 10,
    plan_code: 'premium_individual',
    plan_id: 2,
    plan_price_id: 3,
    billing_period: 'monthly',
    amount: 9.99,
    currency: 'USD',
    status: 'draft',
    next_action: 'attach_payment_method',
    subscription_id: null,
    invoice_id: null,
    payment_attempt_id: null,
    payment_method_id: null,
    idempotency_key: 'key-1',
    failure_code: null,
    created_at: '',
    updated_at: '',
    expires_at: null,
    completed_at: null,
    is_simulated: true,
    payment_method: null,
    ...overrides,
  };
}

describe('checkoutReducer', () => {
  it('starts at review with empty session and no PAN fields', () => {
    expect(initialCheckoutState.step).toBe('review');
    expect(initialCheckoutState.session).toBeNull();
    expect(JSON.stringify(initialCheckoutState)).not.toMatch(/pan|cvv/i);
  });

  it('applies session status to UI step', () => {
    let state = checkoutReducer(initialCheckoutState, {
      type: 'APPLY_SESSION',
      session: session({ status: 'ready', next_action: 'confirm' }),
    });
    expect(state.step).toBe('payment');

    state = checkoutReducer(state, {
      type: 'APPLY_SESSION',
      session: session({ status: 'processing', next_action: 'wait_or_resume' }),
    });
    expect(state.step).toBe('processing');

    state = checkoutReducer(state, {
      type: 'APPLY_SESSION',
      session: session({ status: 'succeeded', next_action: 'view_result' }),
    });
    expect(state.step).toBe('result');

    state = checkoutReducer(state, {
      type: 'APPLY_SESSION',
      session: session({ status: 'failed', next_action: 'retry_or_change_method', failure_code: 'declined' }),
    });
    expect(state.step).toBe('result');
  });

  it('tracks disclosure, submitting and errors without storing card data', () => {
    let state = checkoutReducer(initialCheckoutState, {
      type: 'SET_DISCLOSURE_SEEN',
    });
    expect(state.disclosureSeen).toBe(true);

    state = checkoutReducer(state, { type: 'SET_SUBMITTING', submitting: true });
    expect(state.submitting).toBe(true);

    state = checkoutReducer(state, {
      type: 'SET_ATTACHED_METHOD',
      method: { brand: 'visa', last4: '4242', display_label: 'Visa ···· 4242' },
    });
    expect(state.attachedMethod?.last4).toBe('4242');
    expect(JSON.stringify(state)).not.toContain('4242424242424242');

    state = checkoutReducer(state, { type: 'SET_ERROR', errorCode: 'payment_declined' });
    expect(state.errorCode).toBe('payment_declined');
    expect(state.submitting).toBe(false);

    state = checkoutReducer(state, { type: 'RESET' });
    expect(state).toEqual(initialCheckoutState);
  });

  it('GO_STEP changes step explicitly', () => {
    const state = checkoutReducer(initialCheckoutState, {
      type: 'GO_STEP',
      step: 'billing',
    });
    expect(state.step).toBe('billing');
  });
});
