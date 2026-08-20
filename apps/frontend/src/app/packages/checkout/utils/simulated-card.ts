import { SafePaymentMethodPayload } from '../models/checkout.models';

export type CardBrand = 'visa' | 'mastercard' | 'amex';

/** Documented test PANs → opaque simulation tokens (browser-only). */
const EXACT_TOKEN_BY_PAN: Record<string, string> = {
  // Visa
  '4242424242424242': 'sim_tok_succeeded',
  '4000000000000002': 'sim_tok_declined',
  '4000000000009995': 'sim_tok_insufficient_funds',
  '4000000000000077': 'sim_tok_processing',
  // Mastercard
  '5555555555554444': 'sim_tok_succeeded',
  '5105105105105100': 'sim_tok_succeeded',
  '2223003122003222': 'sim_tok_succeeded',
  '5200828282828210': 'sim_tok_declined',
  // Amex
  '378282246310005': 'sim_tok_succeeded',
  '371449635398431': 'sim_tok_declined',
};

/** Suggested demo PAN per brand (success path). */
export const DEMO_PAN_BY_BRAND: Record<CardBrand, string> = {
  visa: '4242424242424242',
  mastercard: '5555555555554444',
  amex: '378282246310005',
};

export type SensitiveFieldRef = { value: string } | HTMLInputElement;

export interface CardValidationResult {
  ok: boolean;
  errors: string[];
}

export function digitsOnly(value: string): string {
  return String(value ?? '').replace(/\D/g, '');
}

export function panMaxDigits(brand: CardBrand): number {
  return brand === 'amex' ? 15 : 16;
}

export function cvvMaxDigits(brand: CardBrand): number {
  return brand === 'amex' ? 4 : 3;
}

/** Format PAN for display (groups of 4; Amex 4-6-5). */
export function formatPanDisplay(panDigits: string, brand: CardBrand): string {
  const d = digitsOnly(panDigits).slice(0, panMaxDigits(brand));
  if (brand === 'amex') {
    const a = d.slice(0, 4);
    const b = d.slice(4, 10);
    const c = d.slice(10, 15);
    return [a, b, c].filter(Boolean).join(' ');
  }
  return d.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
}

/** Luhn check on digit string (PAN without spaces). */
export function luhnValid(panDigits: string): boolean {
  const digits = digitsOnly(panDigits);
  if (digits.length < 13 || digits.length > 19) return false;
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = Number(digits[i]);
    if (Number.isNaN(n)) return false;
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}

export function resolveSimulationToken(panDigits: string): string | null {
  const digits = digitsOnly(panDigits);
  if (EXACT_TOKEN_BY_PAN[digits]) return EXACT_TOKEN_BY_PAN[digits];
  return null;
}

export function inferBrand(panDigits: string, brandHint?: string): string {
  if (brandHint && brandHint.trim()) return brandHint.trim().toLowerCase();
  const d = digitsOnly(panDigits);
  if (/^3[47]/.test(d)) return 'amex';
  if (d.startsWith('4')) return 'visa';
  if (/^5[1-5]/.test(d) || /^2[2-7]/.test(d)) return 'mastercard';
  return 'card';
}

export function brandMatchesPan(panDigits: string, brand: CardBrand): boolean {
  const inferred = inferBrand(panDigits);
  return inferred === brand;
}

function expiryValid(expMonth: number, expYear: number, now = new Date()): boolean {
  if (!Number.isInteger(expMonth) || expMonth < 1 || expMonth > 12) return false;
  const y = now.getFullYear();
  if (!Number.isInteger(expYear) || expYear < y || expYear > y + 20) return false;
  const m = now.getMonth() + 1;
  if (expYear > y) return true;
  return expMonth >= m;
}

export function validateCardInput(
  pan: string,
  cvv: string,
  expMonth: number,
  expYear: number,
  brand: CardBrand = 'visa',
): CardValidationResult {
  const errors: string[] = [];
  const digits = digitsOnly(pan);
  const cvvDigits = digitsOnly(cvv);
  const expectedLen = panMaxDigits(brand);
  const expectedCvv = cvvMaxDigits(brand);

  if (digits.length !== expectedLen || !luhnValid(digits)) {
    errors.push('invalid_pan');
  } else if (!brandMatchesPan(digits, brand)) {
    errors.push('brand_mismatch');
  }
  if (!resolveSimulationToken(digits)) {
    errors.push('unknown_test_pan');
  }
  if (cvvDigits.length !== expectedCvv) {
    errors.push('invalid_cvv');
  }
  if (!expiryValid(expMonth, expYear)) {
    errors.push('invalid_expiry');
  }

  return { ok: errors.length === 0, errors };
}

/**
 * Map in-memory card fields to a safe API payload.
 * NEVER returns pan or cvv.
 */
export function mapToSafeMethod(
  pan: string,
  cvv: string,
  expMonth: number,
  expYear: number,
  brand: CardBrand = 'visa',
): SafePaymentMethodPayload {
  const validation = validateCardInput(pan, cvv, expMonth, expYear, brand);
  if (!validation.ok) {
    throw new Error(`card_validation_failed:${validation.errors.join(',')}`);
  }
  const digits = digitsOnly(pan);
  const token = resolveSimulationToken(digits)!;
  const resolvedBrand = inferBrand(digits, brand);
  const last4 = digits.slice(-4);
  const brandLabel = resolvedBrand.charAt(0).toUpperCase() + resolvedBrand.slice(1);
  return {
    brand: resolvedBrand,
    last4,
    exp_month: expMonth,
    exp_year: expYear,
    display_label: `${brandLabel} ···· ${last4}`,
    simulation_token: token,
    is_default: true,
  };
}

/** Clear a single sensitive field ref (input or { value }). */
export function clearSensitive(ref: SensitiveFieldRef | null | undefined): void {
  if (!ref) return;
  ref.value = '';
}

/** Clear several sensitive field refs. */
export function clearSensitiveFields(
  ...refs: Array<SensitiveFieldRef | null | undefined>
): void {
  for (const ref of refs) clearSensitive(ref);
}
