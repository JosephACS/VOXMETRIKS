import {
  CheckoutSession,
  CheckoutUiStep,
  PaymentMethodSafe,
} from '../models/checkout.models';

/** UI state for the checkout journey — never holds PAN/CVV. */
export interface CheckoutUiState {
  step: CheckoutUiStep;
  session: CheckoutSession | null;
  /** Attached safe method summary (no simulation_token required in state). */
  attachedMethod: PaymentMethodSafe | null;
  disclosureSeen: boolean;
  submitting: boolean;
  errorCode: string | null;
}

export type CheckoutAction =
  | { type: 'RESET' }
  | { type: 'SET_SESSION'; session: CheckoutSession }
  | { type: 'GO_STEP'; step: CheckoutUiStep }
  | { type: 'SET_ATTACHED_METHOD'; method: PaymentMethodSafe | null }
  | { type: 'SET_DISCLOSURE_SEEN'; seen?: boolean }
  | { type: 'SET_SUBMITTING'; submitting: boolean }
  | { type: 'SET_ERROR'; errorCode: string | null }
  | { type: 'APPLY_SESSION'; session: CheckoutSession };

export const initialCheckoutState: CheckoutUiState = {
  step: 'review',
  session: null,
  attachedMethod: null,
  disclosureSeen: false,
  submitting: false,
  errorCode: null,
};

function stepFromSession(session: CheckoutSession): CheckoutUiStep {
  const status = String(session.status);
  switch (status) {
    case 'succeeded':
    case 'canceled':
    case 'expired':
    case 'failed':
      return 'result';
    case 'processing':
      return 'processing';
    case 'ready':
      return 'payment';
    case 'draft':
    case 'awaiting_method':
      return 'payment';
    default:
      return 'review';
  }
}

export function checkoutReducer(
  state: CheckoutUiState,
  action: CheckoutAction,
): CheckoutUiState {
  switch (action.type) {
    case 'RESET':
      return { ...initialCheckoutState };
    case 'SET_SESSION':
      return {
        ...state,
        session: action.session,
        attachedMethod: action.session.payment_method ?? state.attachedMethod,
        errorCode: action.session.failure_code ?? state.errorCode,
      };
    case 'APPLY_SESSION': {
      const session = action.session;
      return {
        ...state,
        session,
        attachedMethod: session.payment_method ?? state.attachedMethod,
        step: stepFromSession(session),
        submitting: false,
        errorCode: session.failure_code ?? null,
      };
    }
    case 'GO_STEP':
      return { ...state, step: action.step };
    case 'SET_ATTACHED_METHOD':
      return { ...state, attachedMethod: action.method };
    case 'SET_DISCLOSURE_SEEN':
      return { ...state, disclosureSeen: action.seen !== false };
    case 'SET_SUBMITTING':
      return { ...state, submitting: action.submitting };
    case 'SET_ERROR':
      return {
        ...state,
        errorCode: action.errorCode,
        submitting: action.errorCode ? false : state.submitting,
      };
    default: {
      const _exhaustive: never = action;
      void _exhaustive;
      return state;
    }
  }
}
