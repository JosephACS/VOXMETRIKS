/** Divide nombres colaborativos "Artista A;Artista B" en artistas individuales. */
export function splitArtistNames(raw?: string | null): string[] {
  if (!raw?.trim()) return [];
  return raw
    .split(/[;,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function primaryArtistName(raw?: string | null): string {
  const parts = splitArtistNames(raw);
  return parts[0] ?? raw?.trim() ?? '—';
}

export function isCollaboration(raw?: string | null): boolean {
  return splitArtistNames(raw).length > 1;
}
