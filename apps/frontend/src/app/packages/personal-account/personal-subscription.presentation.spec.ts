import { personalOwnerTypeLabelKey } from './personal-subscription.presentation';

describe('personalOwnerTypeLabelKey', () => {
  it('maps known owner types', () => {
    expect(personalOwnerTypeLabelKey('user')).toBe('personal.subscription.owner.user');
    expect(personalOwnerTypeLabelKey('organization')).toBe(
      'personal.subscription.owner.organization',
    );
  });

  it('falls back honestly for unknown or empty values', () => {
    expect(personalOwnerTypeLabelKey(null)).toBe('common.notAvailable');
    expect(personalOwnerTypeLabelKey('')).toBe('common.notAvailable');
    expect(personalOwnerTypeLabelKey('household')).toBe('common.notAvailable');
  });
});
