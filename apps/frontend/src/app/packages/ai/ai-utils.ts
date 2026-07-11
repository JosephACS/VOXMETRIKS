/** Client-side mirror of backend sanitizer for tests. */
export function sanitize_ai_context(data: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(data)) {
    if (['token', 'password', 'email'].includes(k.toLowerCase())) continue;
    out[k] = v;
  }
  return out;
}
