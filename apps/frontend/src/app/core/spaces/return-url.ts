/** Local returnUrl capture — never persist absolute or protocol-relative URLs. */

export const RETURN_URL_STORAGE_KEY = 'voxmetriks_return_url';

export function isSafeReturnUrl(url: string | null | undefined): url is string {
  if (!url) return false;
  const trimmed = url.trim();
  if (!trimmed.startsWith('/')) return false;
  if (trimmed.startsWith('//')) return false;
  if (trimmed.includes('\\')) return false;
  const lower = trimmed.toLowerCase();
  if (lower.startsWith('/http:') || lower.startsWith('/https:')) return false;
  if (lower.includes('javascript:')) return false;
  return true;
}

export function captureReturnUrl(url: string | null | undefined): void {
  if (!isSafeReturnUrl(url)) return;
  try {
    sessionStorage.setItem(RETURN_URL_STORAGE_KEY, url);
  } catch {
    /* ignore quota */
  }
}

export function consumeReturnUrl(): string | null {
  try {
    const raw = sessionStorage.getItem(RETURN_URL_STORAGE_KEY);
    sessionStorage.removeItem(RETURN_URL_STORAGE_KEY);
    return isSafeReturnUrl(raw) ? raw : null;
  } catch {
    return null;
  }
}

export function peekReturnUrl(): string | null {
  try {
    const raw = sessionStorage.getItem(RETURN_URL_STORAGE_KEY);
    return isSafeReturnUrl(raw) ? raw : null;
  } catch {
    return null;
  }
}
