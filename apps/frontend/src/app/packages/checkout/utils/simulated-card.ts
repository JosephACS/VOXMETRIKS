import { SafePaymentMethodPayload } from '../models/checkout.models';

/** Documented test PANs → opaque simulation tokens (browser-only). */
const EXACT_TOKEN_BY_PAN: Record<string, string> = {
  '4000000000000002': 'sim_tok_declined',
  '4000000000009995': 'sim_tok_insufficient_funds',
  '4000000000000077': 'sim_tok_processing',
};

export type SensitiveFieldRef = { value: string } | HTMLInputElement;

export interface CardValidationResult {
  ok: boolean;
  errors: string[];
}

export function digitsOnly(value: string): string {
  return String(value ?? '').replace(/\D/g, '');
}

/** Luhn check on digit string (PAN without spaces). */
export function luhnValid(panDigits: string): boolean {
  const digits = digitsOnly(panDigits);
  if (digits.length < 12 || digits.length > 19) return false;
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
  if (digits.endsWith('4242') && luhnValid(digits)) return 'sim_tok_succeeded';
  return null;
}

export function inferBrand(panDigits: string, brandHint?: string): string {
  if (brandHint && brandHint.trim()) return brandHint.trim().toLowerCase();
  const d = digitsOnly(panDigits);
  if (d.startsWith('4')) return 'visa';
  if (/^5[1-5]/.test(d) || /^2[2-7]/.test(d)) return 'mastercard';
  if (/^3[47]/.test(d)) return 'amex';
  return 'card';
}

function expiryValid(expMonth: number, expYear: number, now = new Date()): boolean {
  if (!Number.isInteger(expMonth) || expMonth < 1 || expMonth > 12) return false;
  if (!Number.isInteger(expYear) || expYear < 2024 || expYear > 2100) return false;
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  if (expYear > y) return true;
  if (expYear < y) return false;
  return expMonth >= m;
}

export function validateCardInput(
  pan: string,
  cvv: string,
  expMonth: number,
  expYear: number,
): CardValidationResult {
  const errors: string[] = [];
  const digits = digitsOnly(pan);
  const cvvDigits = digitsOnly(cvv);

  if (!luhnValid(digits)) {
    errors.push('invalid_pan');
  }
  if (!resolveSimulationToken(digits)) {
    errors.push('unknown_test_pan');
  }
  if (cvvDigits.length < 3 || cvvDigits.length > 4) {
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
  brand?: string,
): SafePaymentMethodPayload {
  const validation = validateCardInput(pan, cvv, expMonth, expYear);
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
