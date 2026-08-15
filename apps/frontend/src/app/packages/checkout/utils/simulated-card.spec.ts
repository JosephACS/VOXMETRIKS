import { describe, expect, it } from 'vitest';
import {
  clearSensitive,
  clearSensitiveFields,
  luhnValid,
  mapToSafeMethod,
  resolveSimulationToken,
  validateCardInput,
} from './simulated-card';

const SUCCESS_PAN = '4242424242424242';
const DECLINED_PAN = '4000000000000002';
const INSUFFICIENT_PAN = '4000000000009995';
const PROCESSING_PAN = '4000000000000077';

describe('simulated-card', () => {
  it('validates Luhn for documented test PANs', () => {
    expect(luhnValid(SUCCESS_PAN)).toBe(true);
    expect(luhnValid(DECLINED_PAN)).toBe(true);
    expect(luhnValid(INSUFFICIENT_PAN)).toBe(true);
    expect(luhnValid(PROCESSING_PAN)).toBe(true);
    expect(luhnValid('4242424242424241')).toBe(false);
  });

  it('maps documented PANs to simulation tokens', () => {
    expect(resolveSimulationToken(SUCCESS_PAN)).toBe('sim_tok_succeeded');
    expect(resolveSimulationToken(DECLINED_PAN)).toBe('sim_tok_declined');
    expect(resolveSimulationToken(INSUFFICIENT_PAN)).toBe('sim_tok_insufficient_funds');
    expect(resolveSimulationToken(PROCESSING_PAN)).toBe('sim_tok_processing');
  });

  it('mapToSafeMethod never returns pan or cvv', () => {
    const year = new Date().getFullYear() + 2;
    const safe = mapToSafeMethod(SUCCESS_PAN, '123', 12, year);
    expect(safe.simulation_token).toBe('sim_tok_succeeded');
    expect(safe.last4).toBe('4242');
    expect(safe.brand).toBe('visa');
    expect(JSON.stringify(safe)).not.toContain(SUCCESS_PAN);
    expect(JSON.stringify(safe)).not.toContain('123');
    expect('pan' in safe).toBe(false);
    expect('cvv' in safe).toBe(false);
  });

  it('validateCardInput rejects bad expiry and unknown pans', () => {
    const bad = validateCardInput(SUCCESS_PAN, '12', 13, 2020);
    expect(bad.ok).toBe(false);
    expect(bad.errors.length).toBeGreaterThan(0);

    const unknown = validateCardInput('4111111111111111', '123', 12, new Date().getFullYear() + 1);
    expect(unknown.ok).toBe(false);
    expect(unknown.errors).toContain('unknown_test_pan');
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
