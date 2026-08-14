import { describe, expect, it } from 'vitest';
import {
  classificationLabelEs,
  countStatLabel,
  formatAnalyzedPeriod,
  formatDdMmYyyy,
  formatSeriesLabel,
  formatUpdatedAtEs,
  formatYearMonthEs,
  inclusiveEndIso,
  isTechnicalColumnKey,
  parseYmd,
} from './complex-reports-presentation';

describe('complex-reports-presentation', () => {
  it('formats dates without UTC day shift', () => {
    expect(parseYmd('2026-01-27')).toEqual({ y: 2026, m: 1, d: 27 });
    expect(formatDdMmYyyy('2026-01-27')).toBe('27/01/2026');
    expect(inclusiveEndIso('2026-08-03')).toBe('2026-08-02');
    expect(formatAnalyzedPeriod('2026-01-27', '2026-08-03')).toBe(
      'Periodo analizado: 27/01/2026 al 02/08/2026',
    );
  });

  it('formats updated_at in Spanish without raw ISO', () => {
    const s = formatUpdatedAtEs('2026-08-02T20:48:00.000Z');
    expect(s).toMatch(/de agosto de 2026/);
    expect(s).not.toContain('T');
    expect(s).not.toContain('Z');
  });

  it('maps count labels for video reports', () => {
    expect(countStatLabel('streams-by-day')).toBe('Días con datos');
    expect(countStatLabel('top-tracks-period')).toBe('Canciones mostradas');
    expect(countStatLabel('releases-status-month')).toBe('Grupos encontrados');
    expect(countStatLabel('subscription-growth-month')).toBe('Meses con datos');
    expect(countStatLabel('top-artists-period')).toBe('Artistas mostrados');
  });

  it('hides technical id columns', () => {
    expect(isTechnicalColumnKey('id')).toBe(true);
    expect(isTechnicalColumnKey('track_id')).toBe(true);
    expect(isTechnicalColumnKey('organization_id')).toBe(true);
    expect(isTechnicalColumnKey('cancion')).toBe(false);
    expect(isTechnicalColumnKey('reproducciones')).toBe(false);
  });

  it('humanizes months and classifications', () => {
    expect(formatYearMonthEs('2026-07')).toBe('Julio de 2026');
    expect(formatSeriesLabel('2026-07')).toBe('Julio de 2026');
    expect(classificationLabelEs('demo')).toBe('Datos sintéticos');
    expect(classificationLabelEs('synthetic')).toBe('Datos sintéticos');
    expect(classificationLabelEs('operational')).toBe('Datos operacionales');
  });
});
