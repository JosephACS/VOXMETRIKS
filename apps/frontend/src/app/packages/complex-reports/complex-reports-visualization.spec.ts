import { describe, expect, it } from 'vitest';
import {
  artistDistributionUseful,
  buildLeaderboardRows,
  buildReportInsight,
  buildReportKpis,
  collapseOtros,
  cumulativeValues,
  visualizationIdForReport,
  visualizationTestId,
  temporalPeriodCount,
  useTemporalSnapshot,
  useReleaseStatusComposition,
  humanizeStatusLabel,
} from './complex-reports-visualization';

describe('complex-reports-visualization', () => {
  it('maps report ids to visualization kinds', () => {
    expect(visualizationIdForReport('streams-by-day')).toBe('temporal-line');
    expect(visualizationIdForReport('income-by-month')).toBe('monthly-combo');
    expect(visualizationIdForReport('top-tracks-period')).toBe('leaderboard');
    expect(visualizationIdForReport('top-genres-period')).toBe('genre-composition');
    expect(visualizationIdForReport('campaign-roi')).toBe('unavailable');
    expect(visualizationTestId('leaderboard')).toBe('visualization-leaderboard');
    expect(visualizationTestId('genre-composition')).toBe('visualization-genre-composition');
  });

  it('uses temporal snapshot only below 3 periods', () => {
    expect(useTemporalSnapshot('income-by-month', [{ label: '2026-01', value: 1 }])).toBe(true);
    expect(
      useTemporalSnapshot('income-by-month', [
        { label: '2026-01', value: 1 },
        { label: '2026-02', value: 2 },
        { label: '2026-03', value: 3 },
      ]),
    ).toBe(false);
    expect(useReleaseStatusComposition('releases-status-month', [{ label: '2026-07 · draft', value: 1 }])).toBe(
      true,
    );
    expect(temporalPeriodCount([{ label: '2026-07 · draft', value: 1 }, { label: '2026-07 · published', value: 2 }])).toBe(1);
    expect(humanizeStatusLabel('changes_requested')).toBe('Cambios solicitados');
  });

  it('builds stream peak insight from series', () => {
    const insight = buildReportInsight(
      'streams-by-day',
      [
        { label: '2026-06-10', value: 100 },
        { label: '2026-06-16', value: 9972 },
        { label: '2026-06-20', value: 200 },
      ],
      {},
    );
    expect(insight).toContain('9.972');
    expect(insight).toContain('16 jun');
  });

  it('builds top-tracks concentration insight against full pool', () => {
    const series = [
      { label: 'A', value: 50 },
      { label: 'B', value: 30 },
      { label: 'C', value: 20 },
      { label: 'D', value: 100 },
    ];
    // Top3 of pool = 50+30+20=100 over total 200 → 50 %
    const insight = buildReportInsight('top-tracks-period', series, {});
    expect(insight).toMatch(/50 %/);
    expect(insight).toContain('Top 4');
  });

  it('builds selective KPIs for streams and top-tracks', () => {
    const streamKpis = buildReportKpis(
      'streams-by-day',
      { total: 1000, average: 50, max: 200, count: 20 },
      [],
    );
    expect(streamKpis).toHaveLength(4);
    expect(streamKpis.map((k) => k.label)).toEqual([
      'Reproducciones',
      'Promedio diario',
      'Pico del periodo',
      'Días con datos',
    ]);

    const trackKpis = buildReportKpis(
      'top-tracks-period',
      { total: 100, average: 10, max: 40, count: 10 },
      [
        { label: 'a', value: 40 },
        { label: 'b', value: 30 },
        { label: 'c', value: 20 },
        { label: 'd', value: 10 },
      ],
    );
    expect(trackKpis).toHaveLength(3);
    expect(trackKpis[2].format).toBe('percent');
  });

  it('detects flat artist distributions', () => {
    expect(artistDistributionUseful([10, 10, 10, 10])).toBe(false);
    expect(artistDistributionUseful([100, 40, 20, 10])).toBe(true);
  });

  it('builds leaderboard rows and cumulative combo values', () => {
    const rows = buildLeaderboardRows(
      [
        { track_id: 1, cancion: 'A', artista: 'X', reproducciones: 100 },
        { track_id: 2, cancion: 'B', artista: 'Y', reproducciones: 50 },
      ],
      [
        { label: 'A', value: 100 },
        { label: 'B', value: 50 },
      ],
      10,
    );
    expect(rows[0].barPct).toBe(100);
    expect(rows[1].barPct).toBe(50);
    expect(cumulativeValues([1, 2, 3])).toEqual([1, 3, 6]);
    expect(collapseOtros(
      [
        { label: '1', value: 10 },
        { label: '2', value: 9 },
        { label: '3', value: 8 },
        { label: '4', value: 7 },
        { label: '5', value: 6 },
        { label: '6', value: 5 },
        { label: '7', value: 4 },
        { label: '8', value: 3 },
      ],
      5,
    ).at(-1)?.name).toBe('Otros');
  });
});
