/**
 * Product-facing display helpers.
 * Softens fixture/demo naming in the UI without mutating stored data or IDs.
 */

const ORG_DEMO_ALIASES = /^(voxmetriks\s+demo|vox\s*demo)$/i;
const USER_DEMO_ALIASES = /^(demo|demo\.listener|demo\.user)$/i;

const MONTHS_ES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
];

const MONTHS_EN = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

/** Organization display name for chrome/selectors. */
export function productOrgDisplayName(raw: string | null | undefined): string {
  const name = (raw ?? '').trim();
  if (!name) return '';
  if (ORG_DEMO_ALIASES.test(name)) return 'VOXMETRIKS Studio';
  return name.replace(/\s*\((?:Demo|Demostración)\)\s*$/i, '').trim() || name;
}

/** Listener/account display name (never expose bare "demo"). */
export function productUserDisplayName(
  username: string | null | undefined,
  fallback = 'Oyente',
): string {
  const name = (username ?? '').trim();
  if (!name || USER_DEMO_ALIASES.test(name)) return fallback;
  return name;
}

/**
 * Humanize fixture release titles like "Demo release 2026-05" or "[DEMO] Scheduled Single".
 * Returns null when the title is not a known fixture pattern.
 */
export function humanizeFixtureReleaseTitle(
  raw: string | null | undefined,
  lang: 'es' | 'en' = 'es',
): string | null {
  const title = (raw ?? '').trim();
  if (!title) return null;
  const m = title.match(/^demo\s+release\s+(\d{4})-(\d{2})\b/i);
  if (m) {
    const year = m[1];
    const monthIdx = Number(m[2]) - 1;
    if (monthIdx < 0 || monthIdx > 11) return null;
    if (lang === 'en') {
      return `${MONTHS_EN[monthIdx]} ${year} release`;
    }
    return `Lanzamiento ${MONTHS_ES[monthIdx]} ${year}`;
  }

  const bracket = title.match(/^\[DEMO(?:-\d+)?\]\s*(.+)$/i);
  if (bracket) {
    const rest = bracket[1]
      .replace(/\s*\((?:Demo|Demostración|Synthetic)\)\s*$/i, '')
      .trim();
    return rest || (lang === 'en' ? 'Release' : 'Lanzamiento');
  }
  return null;
}

/** Soften fixture artist names for product chrome (does not mutate storage). */
export function productArtistDisplayName(raw: string | null | undefined): string {
  const name = (raw ?? '').trim();
  if (!name) return '';
  let out = name
    .replace(/\s*\((?:Demo|Demostración|Synthetic|Sintético)\)\s*$/i, '')
    .replace(/\s+\[DEMO[^\]]*\]\s*$/i, '')
    .trim();
  if (/^demo\s+artist\b/i.test(out)) {
    return out.replace(/^demo\s+artist\b/i, 'Artista del sello').trim();
  }
  out = out.replace(/^demo\s+/i, '').trim();
  return out || name;
}

/** Soften org slug for display (internal slug may keep demo). */
export function productOrgSlugDisplay(raw: string | null | undefined): string {
  const slug = (raw ?? '').trim();
  if (!slug) return '';
  if (/^voxmetriks-demo$/i.test(slug)) return 'voxmetriks-studio';
  return slug.replace(/-demo(?=-|$)/gi, '').replace(/^demo-/i, '') || slug;
}

/** Soften invoice numbers like DEMO-INV-PAID-001 for UI. */
export function productInvoiceNumber(raw: string | null | undefined, fallbackId?: number | string): string {
  const num = (raw ?? '').trim();
  if (!num) return fallbackId != null ? `Factura #${fallbackId}` : '';
  return num.replace(/^DEMO-/i, '').replace(/-DEMO-/gi, '-') || num;
}
