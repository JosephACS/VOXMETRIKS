export function fmtNumber(val?: number | null): string {
  if (val == null) return '—';
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
  return val.toLocaleString('es-ES');
}

export function formatDurationMin(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  if (h > 0) return `${h} h ${m} min`;
  return `${m} min`;
}

export function trackDurationLabel(id: number): string {
  const sec = 180 + (id % 120);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function trackProgressPct(id: number): number {
  return 25 + (id % 65);
}

export function barHeightPct(v: number): number {
  return Math.max(v, 4);
}

export function artistAffinityPct(index: number): number {
  return Math.max(62, 98 - index * 7);
}

export function recoCompatibilityPct(id: number): number {
  return 86 + (id % 14);
}
