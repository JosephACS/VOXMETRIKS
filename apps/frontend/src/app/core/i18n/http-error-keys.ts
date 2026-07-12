/** HTTP status → i18n key for user-facing API errors (no technical dumps). */

export const HTTP_ERROR_KEYS: Record<number, string> = {
  400: 'httpError.400',
  401: 'httpError.401',
  403: 'httpError.403',
  404: 'httpError.404',
  409: 'httpError.409',
  410: 'httpError.410',
  422: 'httpError.422',
  429: 'httpError.429',
  500: 'httpError.500',
  502: 'httpError.500',
  503: 'httpError.500',
};

export function httpErrorKey(status: number | null | undefined): string {
  if (status == null) return 'httpError.generic';
  return HTTP_ERROR_KEYS[status] ?? 'httpError.generic';
}

/** True when a backend message looks technical and must not be shown raw. */
export function isTechnicalErrorMessage(message: string | null | undefined): boolean {
  if (!message) return true;
  const m = message.toLowerCase();
  return (
    m.includes('integrityerror') ||
    m.includes('httpexception') ||
    m.includes('traceback') ||
    m.includes('stack') ||
    m.includes('organization_id missing') ||
    m.includes('sqlalchemy') ||
    m.includes('duckdb') ||
    m.includes('nullpointer') ||
    /^[a-z_]+(\.[a-z_]+)+$/.test(message.trim()) // dotted code-like
  );
}
