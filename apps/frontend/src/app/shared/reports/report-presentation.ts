/** Spec 044 — hide technical keys from product tables (keep in API payloads). */

const TECHNICAL_EXACT = new Set([
  'id',
  'uuid',
  'organization_id',
  'user_id',
  'track_id',
  'session_id',
  'job_id',
  'invoice_id',
  'submission_id',
  'asset_id',
  'object_id',
  'owner_user_id',
  'reviewer_id',
  'plan_id',
  'instruction_id',
]);

export function isTechnicalColumnKey(key: string): boolean {
  const k = (key || '').toLowerCase();
  if (!k) return false;
  if (TECHNICAL_EXACT.has(k)) return true;
  if (k.endsWith('_id') || k.endsWith('_uuid')) return true;
  if (k === 'id_artista' || k === 'id_album' || k === 'id_genero' || k === 'id_track') return true;
  return false;
}

export function productVisibleColumns<T extends { key: string }>(columns: T[]): T[] {
  return (columns || []).filter((c) => !isTechnicalColumnKey(c.key));
}

export function scopeBadgeLabel(scope: string | null | undefined): string {
  switch ((scope || '').toLowerCase()) {
    case 'organization':
      return 'Organización';
    case 'platform':
      return 'Plataforma';
    case 'global_analytics':
      return 'Analítica global';
    default:
      return scope || '';
  }
}

export function readinessLabelEs(code: string | null | undefined): string {
  switch ((code || '').toLowerCase()) {
    case 'available':
      return 'Disponible';
    case 'empty':
      return 'Sin registros';
    case 'demo':
      return '';
    case 'unavailable':
      return 'No disponible';
    case 'adjusted':
      return 'Aproximación';
    default:
      return code || '';
  }
}
