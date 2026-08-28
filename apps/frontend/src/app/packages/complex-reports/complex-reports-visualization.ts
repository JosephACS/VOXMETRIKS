/** Visualization map, KPIs and computed insights for complex reports (no invented values). */

export type ReportVisualizationId =
  | 'temporal-line'
  | 'monthly-combo'
  | 'leaderboard'
  | 'artist-treemap'
  | 'artist-ranking'
  | 'genre-donut'
  | 'genre-composition'
  | 'percent-trend'
  | 'subscription-columns'
  | 'stacked-status'
  | 'unavailable';

export type ChartPresetType =
  | 'line'
  | 'bar'
  | 'pie'
  | 'hbar'
  | 'stacked-bar'
  | 'combo'
  | 'treemap'
  | 'percent-line';

export function visualizationIdForReport(reportId: string): ReportVisualizationId {
  switch (reportId) {
    case 'streams-by-day':
      return 'temporal-line';
    case 'income-by-month':
      return 'monthly-combo';
    case 'top-tracks-period':
      return 'leaderboard';
    case 'top-artists-period':
      return 'artist-treemap'; // may fall back to ranking when flat
    case 'top-genres-period':
      return 'genre-composition';
    case 'opportunity-win-rate-month':
      return 'percent-trend';
    case 'subscription-growth-month':
      return 'subscription-columns';
    case 'releases-status-month':
      return 'stacked-status';
    case 'campaign-roi':
      return 'unavailable';
    default:
      return 'temporal-line';
  }
}

export function visualizationTestId(viz: ReportVisualizationId): string {
  switch (viz) {
    case 'temporal-line':
      return 'visualization-temporal-line';
    case 'monthly-combo':
      return 'visualization-monthly-combo';
    case 'leaderboard':
      return 'visualization-leaderboard';
    case 'artist-treemap':
      return 'visualization-artist-treemap';
    case 'artist-ranking':
      return 'visualization-artist-treemap';
    case 'genre-donut':
      return 'visualization-genre-donut';
    case 'genre-composition':
      return 'visualization-genre-composition';
    case 'percent-trend':
      return 'visualization-percent-trend';
    case 'subscription-columns':
      return 'visualization-subscription-columns';
    case 'stacked-status':
      return 'visualization-stacked-status';
    case 'unavailable':
      return 'visualization-unavailable';
    default: {
      const _exhaustive: never = viz;
      return _exhaustive;
    }
  }
}

export function chartPresetForVisualization(viz: ReportVisualizationId): ChartPresetType | null {
  switch (viz) {
    case 'temporal-line':
      return 'line';
    case 'monthly-combo':
      return 'combo';
    case 'leaderboard':
      return null;
    case 'artist-treemap':
      return 'treemap';
    case 'artist-ranking':
      return 'hbar';
    case 'genre-donut':
      return 'pie';
    case 'genre-composition':
      return 'hbar';
    case 'percent-trend':
      return 'percent-line';
    case 'subscription-columns':
      return 'bar';
    case 'stacked-status':
      return 'stacked-bar';
    case 'unavailable':
      return null;
    default: {
      const _exhaustive: never = viz;
      return _exhaustive;
    }
  }
}

/** Prefer treemap only when distribution has meaningful spread. */
export function artistDistributionUseful(values: number[]): boolean {
  if (values.length < 2) return false;
  const nums = values.map((v) => Number(v) || 0).filter((v) => v > 0);
  if (nums.length < 2) return false;
  const max = Math.max(...nums);
  const min = Math.min(...nums);
  if (max <= 0) return false;
  // Too flat / tied → ranking instead of treemap
  if (min / max > 0.85) return false;
  const distinct = new Set(nums.map((n) => Math.round(n))).size;
  return distinct >= Math.min(3, nums.length);
}

export function genreCompositionUseful(values: number[]): boolean {
  // Prefer composition/lollipop over donut whenever there are many or flat slices.
  if (values.length > 8) return true;
  if (values.length === 0) return false;
  return !artistDistributionUseful(values);
}

export function genreDonutUseful(values: number[]): boolean {
  if (values.length === 0 || values.length > 8) return false;
  return artistDistributionUseful(values);
}

/** Distinct temporal periods in series labels (YYYY-MM or YYYY-MM-DD). */
export function temporalPeriodCount(series: { label: string; value: number | null }[]): number {
  const keys = new Set<string>();
  for (const p of series) {
    const raw = String(p.label || '').trim();
    const month = raw.split('·')[0]?.trim() || raw;
    const m = month.match(/^(\d{4}-\d{2})/);
    keys.add(m ? m[1] : month);
  }
  return keys.size;
}

export function useTemporalSnapshot(
  reportId: string,
  series: { label: string; value: number | null }[],
): boolean {
  // Releases with <3 months uses compact status composition (not KPI-only snapshot).
  const monthly = new Set([
    'income-by-month',
    'opportunity-win-rate-month',
    'subscription-growth-month',
  ]);
  if (!monthly.has(reportId)) return false;
  return temporalPeriodCount(series) < 3;
}

/** Releases: full monthly stacks only with 3+ months; else compact status mix. */
export function useReleaseStatusComposition(
  reportId: string,
  series: { label: string; value: number | null }[],
): boolean {
  if (reportId !== 'releases-status-month') return false;
  return temporalPeriodCount(series) < 3;
}

export const VOX_ANALYTIC_PALETTE = [
  '#e8a33d',
  '#149E74',
  '#2A9D8F',
  '#5EAAA8',
  '#7A8B87',
  '#A8B5B0',
  '#3D5A56',
  '#88C9B0',
] as const;

const RELEASE_STATUS_ES: Record<string, string> = {
  draft: 'Borrador',
  submitted: 'Enviado',
  changes_requested: 'Cambios solicitados',
  under_review: 'En revisión',
  approved: 'Aprobado',
  scheduled: 'Programado',
  published: 'Publicado',
  suspended: 'Suspendido',
  withdrawn: 'Retirado',
  rejected: 'Rechazado',
  archived: 'Archivado',
  past_due: 'En atraso',
};

export function humanizeStatusLabel(raw: string | null | undefined): string {
  if (!raw) return '—';
  const key = String(raw).trim().toLowerCase();
  if (RELEASE_STATUS_ES[key]) return RELEASE_STATUS_ES[key];
  if (key.includes('_')) {
    return key
      .split('_')
      .filter(Boolean)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }
  return String(raw);
}

export interface ReportKpi {
  key: string;
  value: number | null;
  label: string;
  accent?: boolean;
  format?: 'compact' | 'percent' | 'number';
}

export function buildReportKpis(
  reportId: string,
  summary: Record<string, number | null>,
  series: { label: string; value: number | null }[],
): ReportKpi[] {
  const total = num(summary['total']);
  const average = num(summary['average']);
  const max = num(summary['max']);
  const count = num(summary['count']) ?? series.length;

  switch (reportId) {
    case 'streams-by-day':
      return [
        { key: 'total', value: total, label: 'Reproducciones' },
        { key: 'average', value: average, label: 'Promedio diario' },
        { key: 'max', value: max, label: 'Pico del periodo', accent: true },
        { key: 'count', value: count, label: 'Días con datos' },
      ];
    case 'top-tracks-period': {
      const pool = series.slice(0, 50);
      const featured = Math.min(10, pool.length);
      const poolTotal = pool.reduce((a, p) => a + (Number(p.value) || 0), 0);
      const top3 = pool.slice(0, 3).reduce((a, p) => a + (Number(p.value) || 0), 0);
      const concentration = poolTotal > 0 ? (top3 / poolTotal) * 100 : null;
      return [
        { key: 'total', value: total, label: 'Reproducciones' },
        { key: 'featured', value: featured, label: 'Canciones destacadas' },
        {
          key: 'concentration',
          value: concentration,
          label: 'Concentración del Top 3',
          accent: true,
          format: 'percent',
        },
      ];
    }
    case 'income-by-month':
      return [
        { key: 'total', value: total, label: 'Ingresos totales' },
        { key: 'average', value: average, label: 'Promedio mensual' },
        { key: 'max', value: max, label: 'Máximo mensual', accent: true },
        { key: 'count', value: count, label: 'Meses con datos' },
      ];
    case 'subscription-growth-month':
      return [
        { key: 'total', value: total, label: 'Nuevas suscripciones' },
        { key: 'max', value: max, label: 'Mes máximo', accent: true },
        { key: 'average', value: average, label: 'Promedio' },
        { key: 'count', value: count, label: 'Meses con datos' },
      ];
    case 'opportunity-win-rate-month':
      return [
        { key: 'average', value: average, label: 'Promedio del periodo', format: 'percent', accent: true },
        { key: 'max', value: max, label: 'Máximo mensual', format: 'percent' },
        { key: 'count', value: count, label: 'Meses con datos' },
      ];
    case 'top-artists-period':
    case 'top-genres-period':
      return [
        { key: 'total', value: total, label: 'Reproducciones' },
        { key: 'count', value: Math.min(count ?? 0, series.length), label: reportId.includes('genre') ? 'Géneros' : 'Artistas' },
        { key: 'max', value: max, label: 'Máximo', accent: true },
      ];
    case 'releases-status-month':
      return [
        { key: 'total', value: total, label: 'Lanzamientos' },
        { key: 'count', value: count, label: 'Grupos encontrados' },
        { key: 'max', value: max, label: 'Máximo' },
      ];
    default:
      return [
        { key: 'total', value: total, label: 'Total' },
        { key: 'average', value: average, label: 'Promedio' },
        { key: 'max', value: max, label: 'Máximo' },
      ];
  }
}

export function buildReportInsight(
  reportId: string,
  series: { label: string; value: number | null }[],
  summary: Record<string, number | null>,
): string | null {
  if (!series.length) return null;

  if (reportId === 'streams-by-day') {
    let peak = series[0];
    for (const p of series) {
      if ((Number(p.value) || 0) > (Number(peak.value) || 0)) peak = p;
    }
    const v = Number(peak.value) || 0;
    if (v <= 0) return null;
    return `Pico del periodo: ${formatIntEs(v)} reproducciones el ${formatShortLabel(peak.label)}.`;
  }

  if (reportId === 'top-tracks-period') {
    const pool = series.slice(0, 50);
    const poolTotal = pool.reduce((a, p) => a + (Number(p.value) || 0), 0);
    const top3 = pool.slice(0, 3).reduce((a, p) => a + (Number(p.value) || 0), 0);
    if (poolTotal <= 0 || pool.length < 3) return null;
    const pct = Math.round((top3 / poolTotal) * 100);
    return `Las 3 canciones principales concentran el ${pct} % de las reproducciones del Top ${pool.length}.`;
  }

  if (reportId === 'income-by-month' || reportId === 'subscription-growth-month') {
    let peak = series[0];
    for (const p of series) {
      if ((Number(p.value) || 0) > (Number(peak.value) || 0)) peak = p;
    }
    const v = Number(peak.value) || 0;
    if (v <= 0) return null;
    const noun = reportId === 'income-by-month' ? 'ingresos' : 'suscripciones';
    return `Mes máximo: ${formatShortLabel(peak.label)} con ${formatIntEs(v)} ${noun}.`;
  }

  if (reportId === 'opportunity-win-rate-month') {
    const avg = num(summary['average']);
    if (avg == null) return null;
    return `Tasa media del periodo: ${formatPctEs(avg)}.`;
  }

  if (reportId === 'top-genres-period' || reportId === 'top-artists-period') {
    const lead = series[0];
    const v = Number(lead?.value) || 0;
    if (!lead || v <= 0) return null;
    const total = series.reduce((a, p) => a + (Number(p.value) || 0), 0);
    const pct = total > 0 ? Math.round((v / total) * 100) : 0;
    return `${formatShortLabel(lead.label)} lidera con el ${pct} % de las reproducciones del ranking.`;
  }

  if (reportId === 'releases-status-month') {
    const total = num(summary['total']);
    if (total == null || total <= 0) return null;
    return `Total de lanzamientos en el periodo: ${formatIntEs(total)}.`;
  }

  return null;
}

export interface LeaderboardRow {
  rank: number;
  trackId: number | null;
  title: string;
  artist: string;
  plays: number;
  barPct: number;
}

export function buildLeaderboardRows(
  rows: Record<string, unknown>[],
  series: { label: string; value: number | null }[],
  limit = 10,
): LeaderboardRow[] {
  const max = Math.max(1, ...series.slice(0, limit).map((s) => Number(s.value) || 0));
  if (rows.length) {
    return rows.slice(0, limit).map((r, i) => {
      const plays = Number(r['reproducciones'] ?? r['plays'] ?? series[i]?.value ?? 0) || 0;
      return {
        rank: i + 1,
        trackId: toId(r['track_id'] ?? r['id_track']),
        title: String(r['cancion'] ?? r['title'] ?? series[i]?.label ?? '—'),
        artist: String(r['artista'] ?? r['artist'] ?? '—'),
        plays,
        barPct: Math.round((plays / max) * 100),
      };
    });
  }
  return series.slice(0, limit).map((s, i) => ({
    rank: i + 1,
    trackId: null,
    title: String(s.label || '—'),
    artist: '—',
    plays: Number(s.value) || 0,
    barPct: Math.round(((Number(s.value) || 0) / max) * 100),
  }));
}

export function cumulativeValues(values: number[]): number[] {
  let acc = 0;
  return values.map((v) => {
    acc += v;
    return acc;
  });
}

export function collapseOtros(
  series: { label: string; value: number | null }[],
  maxSlices = 7,
): { name: string; value: number }[] {
  const sorted = [...series]
    .map((s) => ({ name: String(s.label || '—'), value: Number(s.value) || 0 }))
    .sort((a, b) => b.value - a.value);
  if (sorted.length <= maxSlices) return sorted;
  const head = sorted.slice(0, maxSlices - 1);
  const rest = sorted.slice(maxSlices - 1).reduce((a, p) => a + p.value, 0);
  return [...head, { name: 'Otros', value: rest }];
}

/** Top-N ranking without an Otros bucket (for flat long-tail series). */
export function topNSeries(
  series: { label: string; value: number | null }[],
  n = 8,
): { name: string; value: number }[] {
  return [...series]
    .map((s) => ({ name: String(s.label || '—'), value: Number(s.value) || 0 }))
    .sort((a, b) => b.value - a.value)
    .slice(0, n);
}

function num(v: number | null | undefined): number | null {
  if (v == null || Number.isNaN(Number(v))) return null;
  return Number(v);
}

function toId(v: unknown): number | null {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function formatIntEs(n: number): string {
  const rounded = Math.round(n);
  return String(rounded).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function formatPctEs(n: number): string {
  const v = n <= 1 && n >= 0 ? n * 100 : n;
  return `${v.toLocaleString('es-ES', { maximumFractionDigits: 1 })} %`;
}

function formatShortLabel(label: string): string {
  const raw = String(label || '').trim();
  const ymd = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (ymd) {
    const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
    const mi = Number(ymd[2]) - 1;
    return `${Number(ymd[3])} ${months[mi] || ymd[2]}`;
  }
  const ym = raw.match(/^(\d{4})-(\d{2})$/);
  if (ym) {
    const months = [
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
    return `${months[Number(ym[2]) - 1] || ym[2]} ${ym[1]}`;
  }
  return raw;
}
