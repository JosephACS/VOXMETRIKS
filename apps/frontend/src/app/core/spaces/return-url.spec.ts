import { captureReturnUrl, consumeReturnUrl, isSafeReturnUrl, RETURN_URL_STORAGE_KEY } from './return-url';

describe('returnUrl (050)', () => {
  beforeEach(() => {
    sessionStorage.removeItem(RETURN_URL_STORAGE_KEY);
  });

  it('accepts local paths and rejects unsafe destinations', () => {
    expect(isSafeReturnUrl('/organizations/1')).toBe(true);
    expect(isSafeReturnUrl('/artist-invitations/accept?x=1')).toBe(true);
    expect(isSafeReturnUrl('https://evil.example/phish')).toBe(false);
    expect(isSafeReturnUrl('//evil.example')).toBe(false);
    expect(isSafeReturnUrl('/\\evil')).toBe(false);
    expect(isSafeReturnUrl(null)).toBe(false);
  });

  it('captures and consumes a validated local returnUrl once', () => {
    captureReturnUrl('https://evil.example');
    expect(consumeReturnUrl()).toBeNull();
    captureReturnUrl('/workpanel');
    expect(consumeReturnUrl()).toBe('/workpanel');
    expect(consumeReturnUrl()).toBeNull();
  });
});
