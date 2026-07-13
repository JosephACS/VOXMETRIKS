/**
 * Stable system codes → i18n keys for VOXMETRIKS-generated music UI labels.
 * Proper names (tracks, artists, albums, user playlists) are never mapped here.
 */

export type TranslateFn = (
  key: string,
  params?: Record<string, string | number>,
) => string;

/** Canonical codes emitted by the smart home / mixes APIs. */
export const SYSTEM_LABEL_KEYS: Record<string, string> = {
  discover_weekly: 'smart.section.discover_weekly',
  daily_mix_rock: 'smart.section.daily_mix_rock',
  daily_mix_pop: 'smart.section.daily_mix_pop',
  daily_mix_chill: 'smart.section.daily_mix_chill',
  daily_mix_instrumental: 'smart.section.daily_mix_instrumental',
  continue_listening: 'smart.section.continue_listening',
  continue_listening_sub: 'smart.section.continue_listening_sub',
  recommended_for_you: 'smart.section.recommended_for_you',
  recommended_for_you_sub: 'smart.section.recommended_for_you_sub',
  trending_today: 'smart.section.trending_today',
  genre_new_releases: 'smart.section.genre_new_releases',
  genre_new_releases_sub: 'smart.section.genre_new_releases_sub',
  because_listened: 'smart.section.because_listened',
  because_liked: 'smart.section.because_liked',
  because_frequent_artist: 'smart.section.because_frequent_artist',
  updated_week: 'smart.updatedWeek',
  tag_because: 'smart.tag.because',
  tag_mix: 'smart.tag.mix',
  tag_for_you: 'smart.tag.for_you',
  meta_match: 'smart.meta.match',
  meta_similar: 'smart.meta.similar',
  high_popularity: 'smart.reason.high_popularity',
  high_engagement: 'smart.reason.high_engagement',
  high_engagement_similar_users: 'smart.reason.high_engagement_similar_users',
  trending_artist_genre: 'smart.reason.trending_artist_genre',
  similar_users_plus_trending: 'smart.reason.similar_users_plus_trending',
  trending_popular_pick: 'smart.reason.trending_popular_pick',
  catalog_discovery: 'smart.reason.catalog_discovery',
  familiar_artist: 'smart.reason.familiar_artist',
  new_discovery: 'smart.reason.new_discovery',
  trending: 'smart.reason.trending',
};

/** Legacy display strings (EN/ES) → stable codes for older API payloads. */
const LEGACY_TITLE_TO_CODE: Record<string, string> = {
  'Discover Weekly': 'discover_weekly',
  'Descubrimiento semanal': 'discover_weekly',
  'Daily Mix Rock': 'daily_mix_rock',
  'Mix diario de rock': 'daily_mix_rock',
  'Daily Mix Pop': 'daily_mix_pop',
  'Mix diario de pop': 'daily_mix_pop',
  'Daily Mix Chill': 'daily_mix_chill',
  'Mix diario relajante': 'daily_mix_chill',
  'Daily Mix Instrumental': 'daily_mix_instrumental',
  'Mix diario instrumental': 'daily_mix_instrumental',
  'Seguir escuchando': 'continue_listening',
  'Keep listening': 'continue_listening',
  'Continue listening': 'continue_listening',
  'Recomendado para ti': 'recommended_for_you',
  'Recommended for you': 'recommended_for_you',
  'Trending Today': 'trending_today',
  'Tendencias de hoy': 'trending_today',
  'Basado en tu actividad reciente': 'continue_listening_sub',
  'Based on your recent activity': 'continue_listening_sub',
  'Personalizado con tus gustos': 'recommended_for_you_sub',
  'Personalized to your taste': 'recommended_for_you_sub',
  'Del género que más escuchas': 'genre_new_releases_sub',
  'From the genre you listen to most': 'genre_new_releases_sub',
};

const SECTION_ID_PREFIX_TO_CODE: Array<{ prefix: string; code: string }> = [
  { prefix: 'discover-weekly-', code: 'discover_weekly' },
  { prefix: 'daily-mix-rock-', code: 'daily_mix_rock' },
  { prefix: 'daily-mix-pop-', code: 'daily_mix_pop' },
  { prefix: 'daily-mix-chill-', code: 'daily_mix_chill' },
  { prefix: 'daily-mix-instrumental-', code: 'daily_mix_instrumental' },
  { prefix: 'genre-favorites-', code: 'genre_new_releases' },
  { prefix: 'because-listened-', code: 'because_listened' },
  { prefix: 'because-liked-', code: 'because_liked' },
  { prefix: 'because-artist-', code: 'because_frequent_artist' },
];

export function systemLabelKey(code: string | null | undefined): string | null {
  if (!code) return null;
  const normalized = String(code).trim().toLowerCase().replace(/-/g, '_');
  return SYSTEM_LABEL_KEYS[normalized] ?? null;
}

export function resolveSystemCode(
  code?: string | null,
  title?: string | null,
  sectionId?: string | null,
): string | null {
  if (code) {
    const normalized = String(code).trim().toLowerCase().replace(/-/g, '_');
    if (SYSTEM_LABEL_KEYS[normalized]) return normalized;
  }
  if (title && LEGACY_TITLE_TO_CODE[title]) {
    return LEGACY_TITLE_TO_CODE[title];
  }
  if (sectionId) {
    if (sectionId === 'continue-listening') return 'continue_listening';
    if (sectionId === 'recommended-for-you') return 'recommended_for_you';
    if (sectionId === 'trending-today') return 'trending_today';
    for (const { prefix, code: mapped } of SECTION_ID_PREFIX_TO_CODE) {
      if (sectionId.startsWith(prefix)) return mapped;
    }
  }
  return null;
}

/** Parse ISO week string like `2026-W29` → { year, week }. */
export function parseIsoWeek(
  week: string | null | undefined,
): { year: number; week: number } | null {
  if (!week) return null;
  const m = String(week).trim().match(/^(\d{4})-W(\d{1,2})$/i);
  if (!m) return null;
  return { year: Number(m[1]), week: Number(m[2]) };
}

export function formatUpdatedWeek(week: string | null | undefined, t: TranslateFn): string {
  const parsed = parseIsoWeek(week);
  if (!parsed) {
    const key = systemLabelKey('updated_week');
    return key ? t(key, { week: '—', year: '—' }) : '';
  }
  return t(SYSTEM_LABEL_KEYS['updated_week'], {
    week: parsed.week,
    year: parsed.year,
  });
}

export function translateSystemCode(
  code: string | null | undefined,
  t: TranslateFn,
  params?: Record<string, string | number>,
): string | null {
  const key = systemLabelKey(code);
  if (!key) return null;
  return t(key, params);
}

export function translateReasonCode(
  reason: string | null | undefined,
  t: TranslateFn,
): string | null {
  if (!reason) return null;
  const normalized = String(reason)
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_');
  const viaSystem = translateSystemCode(normalized, t);
  if (viaSystem) return viaSystem;
  const viaReco = t(`reco.reason.${normalized}`);
  const missing = t('common.missingTranslation');
  if (viaReco && viaReco !== missing) return viaReco;
  return null;
}

export interface SmartSectionLabelInput {
  id?: string;
  code?: string | null;
  title?: string | null;
  subtitle?: string | null;
  subtitle_code?: string | null;
  week?: string | null;
  title_params?: Record<string, string | number> | null;
  reason_type?: string | null;
}

export function resolveSectionTitle(
  section: SmartSectionLabelInput,
  t: TranslateFn,
): string {
  const code =
    resolveSystemCode(section.code, section.title, section.id) ??
    (section.reason_type
      ? resolveSystemCode(`because_${section.reason_type}`, null, section.id)
      : null);

  if (code) {
    const translated = translateSystemCode(code, t, section.title_params ?? undefined);
    if (translated) return translated;
  }

  // User-authored or unknown: keep as-is (never invent a translation).
  return section.title?.trim() || '';
}

export function resolveSectionSubtitle(
  section: SmartSectionLabelInput,
  t: TranslateFn,
): string {
  if (section.week || section.subtitle_code === 'updated_week') {
    return formatUpdatedWeek(section.week, t);
  }

  const subCode =
    section.subtitle_code ??
    resolveSystemCode(null, section.subtitle, null) ??
    (section.code === 'continue_listening' || section.id === 'continue-listening'
      ? 'continue_listening_sub'
      : null) ??
    (section.code === 'recommended_for_you' || section.id === 'recommended-for-you'
      ? 'recommended_for_you_sub'
      : null) ??
    (resolveSystemCode(section.code, section.title, section.id) === 'genre_new_releases'
      ? 'genre_new_releases_sub'
      : null);

  if (subCode) {
    const translated = translateSystemCode(subCode, t, section.title_params ?? undefined);
    if (translated) return translated;
  }

  // Artist names / proper nouns passed as subtitle stay untouched.
  return section.subtitle?.trim() || '';
}
