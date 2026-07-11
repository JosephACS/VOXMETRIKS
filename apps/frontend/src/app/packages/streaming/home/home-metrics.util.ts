import { GeneroPopularidad, HistoryEntry } from '../../../shared/models/api.models';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';

export function dedupeHistory(entries: HistoryEntry[], limit = 8): HistoryEntry[] {
  const seen = new Set<string>();
  const out: HistoryEntry[] = [];
  for (const e of entries) {
    const key = displayTrackTitle(e.nombre_track).toLowerCase().trim();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(e);
    if (out.length >= limit) break;
  }
  return out;
}

export function listenStreak(rawHistory: HistoryEntry[]): number {
  const dates = new Set(rawHistory.map((e) => e.viewed_at?.slice(0, 10)).filter(Boolean));
  if (!dates.size) return 0;
  let streak = 0;
  const d = new Date();
  for (;;) {
    const key = d.toISOString().slice(0, 10);
    if (!dates.has(key)) break;
    streak++;
    d.setDate(d.getDate() - 1);
  }
  return streak;
}

export function listenMinutesToday(rawHistory: HistoryEntry[]): number {
  const today = new Date().toISOString().slice(0, 10);
  const n = rawHistory.filter((e) => e.viewed_at?.startsWith(today)).length;
  return Math.round(n * 3.5);
}

export function listenMinutesWeek(rawHistory: HistoryEntry[]): number {
  const weekAgo = Date.now() - 7 * 86_400_000;
  const n = rawHistory.filter((e) => new Date(e.viewed_at).getTime() >= weekAgo).length;
  return Math.round(n * 3.5);
}

export function weeklyDiscoverCount(rawHistory: HistoryEntry[]): number {
  const weekAgo = Date.now() - 7 * 86_400_000;
  const ids = new Set(
    rawHistory
      .filter((e) => new Date(e.viewed_at).getTime() >= weekAgo)
      .map((e) => e.id_track),
  );
  return ids.size;
}

export function hourlyBuckets(rawHistory: HistoryEntry[]): number[] {
  const buckets = Array(24).fill(0);
  for (const e of rawHistory) {
    const h = new Date(e.viewed_at).getHours();
    if (!Number.isNaN(h)) buckets[h]++;
  }
  const max = Math.max(...buckets, 1);
  return buckets.map((v) => Math.round((v / max) * 100));
}

export function peakHourIndex(buckets: number[]): number {
  let idx = 0;
  let best = -1;
  buckets.forEach((v, i) => { if (v > best) { best = v; idx = i; } });
  return idx;
}

export function genreBars(genres: GeneroPopularidad[]) {
  const top = genres.slice(0, 6);
  const max = Math.max(...top.map((g) => g.total_tracks ?? 0), 1);
  return top.map((g) => ({
    name: g.nombre_genero ?? '—',
    pct: Math.max(6, Math.round(((g.total_tracks ?? 0) / max) * 100)),
    tracks: g.total_tracks ?? 0,
  }));
}

export function sparkLine(growthValues: number[]): string {
  if (!growthValues.length) return '';
  const max = Math.max(...growthValues, 1);
  return growthValues
    .map((v, i) => `${i * (440 / Math.max(growthValues.length - 1, 1))},${72 - (v / max) * 56}`)
    .join(' ');
}

export function sparkArea(growthValues: number[], line: string): string {
  if (!growthValues.length) return '';
  const w = (growthValues.length - 1) * (440 / Math.max(growthValues.length - 1, 1));
  return `0,72 ${line} ${w},72`;
}

export function catalogGrowthTrend(growthValues: number[]): number | null {
  if (growthValues.length < 2) return null;
  const prev = growthValues[growthValues.length - 2];
  const cur = growthValues[growthValues.length - 1];
  if (!prev) return null;
  return Math.round(((cur - prev) / prev) * 100);
}

export function historyArtists(rawHistory: HistoryEntry[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const e of rawHistory) {
    const a = e.nombre_artista?.trim();
    if (!a || seen.has(a)) continue;
    seen.add(a);
    out.push(a);
  }
  return out;
}
