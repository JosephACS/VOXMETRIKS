/** Presentation helpers for complex reports — no query/formula changes. */

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

export interface Ymd {
  y: number;
  m: number;
  d: number;
}

/** Parse YYYY-MM-DD without Date/UTC shifts. */
export function parseYmd(value: string | null | undefined): Ymd | null {
  if (!value) return null;
  const m = String(value).trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  if (!y || mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  return { y, m: mo, d };
}

export function ymdToIso(p: Ymd): string {
  return `${p.y}-${String(p.m).padStart(2, '0')}-${String(p.d).padStart(2, '0')}`;
}

export function formatDdMmYyyy(value: string | Ymd | null | undefined): string {
  const p = typeof value === 'string' || value == null ? parseYmd(value || '') : value;
  if (!p) return '—';
  return `${String(p.d).padStart(2, '0')}/${String(p.m).padStart(2, '0')}/${p.y}`;
}

/** Exclusive end (API) → inclusive last day as YYYY-MM-DD. */
export function inclusiveEndIso(periodEndExclusive: string): string {
  const p = parseYmd(periodEndExclusive);
  if (!p) return '';
  const dt = new Date(p.y, p.m - 1, p.d);
  dt.setDate(dt.getDate() - 1);
  return ymdToIso({ y: dt.getFullYear(), m: dt.getMonth() + 1, d: dt.getDate() });
}

export function formatAnalyzedPeriod(periodStart: string, periodEndExclusive: string): string {
  const from = formatDdMmYyyy(periodStart);
  const to = formatDdMmYyyy(inclusiveEndIso(periodEndExclusive));
  return `Periodo analizado: ${from} al ${to}`;
}

/** e.g. "2 de agosto de 2026, 20:48" — local calendar from ISO timestamp. */
export function formatUpdatedAtEs(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  const day = d.getDate();
  const month = MONTHS_ES[d.getMonth()] || '';
  const year = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${day} de ${month} de ${year}, ${hh}:${mm}`;
}

export function countStatLabel(reportId: string): string {
  switch (reportId) {
    case 'streams-by-day':
      return 'Días con datos';
    case 'top-tracks-period':
      return 'Canciones mostradas';
    case 'top-artists-period':
      return 'Artistas mostrados';
    case 'top-genres-period':
      return 'Géneros mostrados';
    case 'releases-status-month':
      return 'Grupos encontrados';
    case 'subscription-growth-month':
      return 'Meses con datos';
    case 'income-by-month':
      return 'Meses con datos';
    case 'opportunity-win-rate-month':
      return 'Meses con datos';
    case 'campaign-roi':
      return 'Campañas';
    default:
      return 'Elementos';
  }
}

export function summaryStatLabels(reportId: string): {
  total: string;
  average: string;
  max: string;
} {
  switch (reportId) {
    case 'streams-by-day':
      return {
        total: 'Total de reproducciones',
        average: 'Promedio diario',
        max: 'Máximo diario',
      };
    case 'top-tracks-period':
      return {
        total: 'Reproducciones',
        average: 'Promedio por canción',
        max: 'Máximo',
      };
    case 'top-artists-period':
      return {
        total: 'Reproducciones',
        average: 'Promedio por artista',
        max: 'Máximo',
      };
    case 'top-genres-period':
      return {
        total: 'Reproducciones',
        average: 'Promedio por género',
        max: 'Máximo',
      };
    case 'subscription-growth-month':
      return {
        total: 'Nuevas suscripciones',
        average: 'Promedio mensual',
        max: 'Máximo mensual',
      };
    case 'income-by-month':
      return {
        total: 'Ingresos totales',
        average: 'Promedio mensual',
        max: 'Máximo mensual',
      };
    case 'opportunity-win-rate-month':
      return {
        total: 'Tasa de cierre',
        average: 'Promedio mensual',
        max: 'Máximo mensual',
      };
    case 'releases-status-month':
      return {
        total: 'Lanzamientos',
        average: 'Promedio por grupo',
        max: 'Máximo',
      };
    default:
      return { total: 'Total', average: 'Promedio', max: 'Máximo' };
  }
}

export function classificationLabelEs(code?: string | null): string {
  switch ((code || '').toLowerCase()) {
    // 'demo' is a legacy backend code for the same synthetic warehouse rows.
    case 'demo':
      return 'Datos sintéticos';
    case 'synthetic':
      return 'Datos sintéticos';
    case 'operational':
      return 'Datos operacionales';
    case 'mixed':
      return 'Datos mixtos';
    case 'real':
      return 'Datos reales';
    case 'simulated':
      return 'Estimado';
    default:
      return code || '—';
  }
}

export function formatYearMonthEs(ym: string): string | null {
  const m = String(ym).trim().match(/^(\d{4})-(\d{2})$/);
  if (!m) return null;
  const monthIdx = Number(m[2]) - 1;
  if (monthIdx < 0 || monthIdx > 11) return null;
  const name = MONTHS_ES[monthIdx];
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} de ${m[1]}`;
}

const TECHNICAL_KEYS = new Set([
  'id',
  'uuid',
  'organization_id',
  'user_id',
  'track_id',
  'session_id',
  'artist_id',
  'member_id',
  'asset_id',
  'release_id',
  'contract_id',
]);

export function isTechnicalColumnKey(key: string): boolean {
  const k = String(key || '').toLowerCase();
  if (!k) return false;
  if (TECHNICAL_KEYS.has(k)) return true;
  if (k.endsWith('_id')) return true;
  if (k === 'pk' || k.endsWith('_pk')) return true;
  return false;
}

export function humanColumnLabel(key: string, label: string): string {
  const k = key.toLowerCase();
  if (k === 'altas') return 'Nuevas suscripciones';
  if (k === 'periodo') return 'Periodo';
  return label || key;
}

export function formatCellDisplay(value: unknown, columnKey?: string): string {
  if (value === null || value === undefined || value === '') return '—';
  const raw = String(value);
  const ym = formatYearMonthEs(raw);
  if (ym) return ym;
  const ymd = parseYmd(raw);
  if (ymd && /^\d{4}-\d{2}-\d{2}/.test(raw)) return formatDdMmYyyy(ymd);
  if (columnKey?.toLowerCase() === 'altas' && raw.toLowerCase() === 'altas') {
    return 'Nuevas suscripciones';
  }
  return raw;
}

export function formatSeriesLabel(label: string): string {
  return formatCellDisplay(label);
}
