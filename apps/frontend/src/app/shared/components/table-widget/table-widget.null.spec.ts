import { describe, expect, it } from 'vitest';
import { TableWidgetComponent } from './table-widget.component';

describe('TableWidgetComponent null cells (spec 014 Phase C)', () => {
  it('cellValue returns null for missing metrics (no invented 0)', () => {
    const cmp = Object.create(TableWidgetComponent.prototype) as TableWidgetComponent<
      Record<string, unknown>
    >;
    const row = { nombre_track: 'A', total_streams: null, engagement_score: undefined };
    expect(
      cmp.cellValue(row, { key: 'total_streams', header: 'Streams', format: 'number' }),
    ).toBeNull();
    expect(
      cmp.cellValue(row, { key: 'engagement_score', header: 'Eng', format: 'number' }),
    ).toBeNull();
    expect(cmp.cellValue(row, { key: 'nombre_track', header: 'Track', format: 'text' })).toBe('A');
  });
});
