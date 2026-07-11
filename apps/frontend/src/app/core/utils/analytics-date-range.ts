/** Derive a warehouse-aligned date range from growth trends or sensible defaults. */
export function analyticsDateRange(
  growthTrends?: { fecha: string }[] | null,
  fallbackDays = 30,
): { start: string; end: string } {
  const trends = growthTrends ?? [];
  if (trends.length >= 2) {
    const sorted = [...trends].sort((a, b) => String(a.fecha).localeCompare(String(b.fecha)));
    return {
      start: String(sorted[0].fecha).slice(0, 10),
      end: String(sorted[sorted.length - 1].fecha).slice(0, 10),
    };
  }

  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - fallbackDays);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

/** MM-DD label for chart axes from API date strings. */
export function formatChartDate(fecha: unknown): string {
  const s = String(fecha ?? '');
  return s.length >= 10 ? s.slice(5, 10) : s;
}

export interface TrendPoint {
  fecha: string;
  total_streams: number;
  unique_users: number;
}

/** Prefer streams API series; fall back to dashboard growth_trends. */
export function mergeTrendSeries(
  streams: { series?: { fecha: unknown; total_streams: number; unique_users?: number }[] } | null,
  growthTrends?: { fecha: unknown; total_streams: number; unique_users?: number }[] | null,
): TrendPoint[] {
  const fromStreams = streams?.series ?? [];
  if (fromStreams.length) {
    return fromStreams.map((p) => ({
      fecha: String(p.fecha),
      total_streams: p.total_streams,
      unique_users: p.unique_users ?? 0,
    }));
  }
  return (growthTrends ?? []).map((p) => ({
    fecha: String(p.fecha),
    total_streams: p.total_streams,
    unique_users: p.unique_users ?? 0,
  }));
}
