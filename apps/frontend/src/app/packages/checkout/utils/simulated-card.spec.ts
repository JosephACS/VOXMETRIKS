import { describe, expect, it } from 'vitest';
import {
  clearSensitive,
  clearSensitiveFields,
  formatPanDisplay,
  luhnValid,
  mapToSafeMethod,
  resolveSimulationToken,
  validateCardInput,
} from './simulated-card';

const SUCCESS_PAN = '4242424242424242';
const MC_SUCCESS = '5555555555554444';
const DECLINED_PAN = '4000000000000002';
const INSUFFICIENT_PAN = '4000000000009995';
const PROCESSING_PAN = '4000000000000077';

describe('simulated-card', () => {
  it('validates Luhn for documented test PANs', () => {
    expect(luhnValid(SUCCESS_PAN)).toBe(true);
    expect(luhnValid(MC_SUCCESS)).toBe(true);
    expect(luhnValid(DECLINED_PAN)).toBe(true);
    expect(luhnValid(INSUFFICIENT_PAN)).toBe(true);
    expect(luhnValid(PROCESSING_PAN)).toBe(true);
    expect(luhnValid('4242424242424241')).toBe(false);
  });

  it('maps documented PANs to simulation tokens', () => {
    expect(resolveSimulationToken(SUCCESS_PAN)).toBe('sim_tok_succeeded');
    expect(resolveSimulationToken(MC_SUCCESS)).toBe('sim_tok_succeeded');
    expect(resolveSimulationToken(DECLINED_PAN)).toBe('sim_tok_declined');
    expect(resolveSimulationToken(INSUFFICIENT_PAN)).toBe('sim_tok_insufficient_funds');
    expect(resolveSimulationToken(PROCESSING_PAN)).toBe('sim_tok_processing');
  });

  it('mapToSafeMethod never returns pan or cvv', () => {
    const year = new Date().getFullYear() + 2;
    const safe = mapToSafeMethod(SUCCESS_PAN, '123', 12, year, 'visa');
    expect(safe.simulation_token).toBe('sim_tok_succeeded');
    expect(safe.last4).toBe('4242');
    expect(safe.brand).toBe('visa');
    expect(JSON.stringify(safe)).not.toContain(SUCCESS_PAN);
    expect(JSON.stringify(safe)).not.toContain('123');
    expect('pan' in safe).toBe(false);
    expect('cvv' in safe).toBe(false);
  });

  it('accepts mastercard success PAN with matching brand', () => {
    const year = new Date().getFullYear() + 2;
    const safe = mapToSafeMethod(MC_SUCCESS, '123', 12, year, 'mastercard');
    expect(safe.brand).toBe('mastercard');
    expect(safe.last4).toBe('4444');
  });

  it('rejects absurdly long pan and brand mismatch', () => {
    const year = new Date().getFullYear() + 2;
    const long = validateCardInput('1252323131313131313131313131313131313', '213', 12, year, 'visa');
    expect(long.ok).toBe(false);
    expect(long.errors).toContain('invalid_pan');

    const mismatch = validateCardInput(MC_SUCCESS, '123', 12, year, 'visa');
    expect(mismatch.ok).toBe(false);
    expect(mismatch.errors).toContain('brand_mismatch');
  });

  it('validateCardInput rejects bad expiry and unknown pans', () => {
    const bad = validateCardInput(SUCCESS_PAN, '12', 13, 2020, 'visa');
    expect(bad.ok).toBe(false);
    expect(bad.errors.length).toBeGreaterThan(0);

    const unknown = validateCardInput('4111111111111111', '123', 12, new Date().getFullYear() + 1, 'visa');
    expect(unknown.ok).toBe(false);
    expect(unknown.errors).toContain('unknown_test_pan');
  });

  it('formats pan display', () => {
    expect(formatPanDisplay(SUCCESS_PAN, 'visa')).toBe('4242 4242 4242 4242');
    expect(formatPanDisplay('378282246310005', 'amex')).toBe('3782 822463 10005');
  });

  it('clearSensitive clears field refs', () => {
    const a = { value: '4242' };
    const b = { value: '999' };
    clearSensitive(a);
    clearSensitiveFields(b, null);
    expect(a.value).toBe('');
    expect(b.value).toBe('');
  });
});
