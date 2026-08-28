/** Strip synthetic suffixes, broken chars and warehouse noise from display text. */
export function sanitizeDisplayText(value?: string | null): string {
  let raw = (value ?? '').trim();
  if (!raw) return '—';
  raw = raw
    .replace(/\uFFFD/g, '')
    .replace(/\s*\[syn-\d+\]\s*$/i, '')
    // Imported catalog rows can contain provider presentation labels. They do
    // not describe the song and make the Spotify-first UI look like a video app.
    .replace(/\s*(?:\[|\()(?:official\s+)?(?:animated\s+|music\s+|lyrics?\s+)?(?:video|audio)(?:\s+clip)?(?:\]|\))/gi, '')
    .replace(/\s*[—–\-·•∙‧]\s*#\d+\s*$/g, '')
    .replace(/\s+#\d{4,}\s*$/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return raw || '—';
}

/** Human-readable track title (trim synthetic suffix for display). */
export function displayTrackTitle(name?: string | null): string {
  return sanitizeDisplayText(name);
}

/** Artist line with optional genre for disambiguation in lists. */
export function displayTrackSubtitle(
  artist?: string | null,
  genre?: string | null,
  trackId?: number,
): string {
  const parts: string[] = [];
  const a = (artist ?? '').trim();
  if (a) parts.push(a);
  const g = (genre ?? '').trim();
  if (g) parts.push(g);
  if (!parts.length && trackId != null) parts.push(`#${trackId}`);
  return parts.join(' · ') || '—';
}
