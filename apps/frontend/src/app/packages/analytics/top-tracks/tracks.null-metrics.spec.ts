import { describe, expect, it } from 'vitest';
import { TracksFeatureComponent } from './tracks.component';

describe('TracksFeatureComponent null metrics (spec 014 Phase C)', () => {
  it('trackMeta does not invent streams when total_streams is null', () => {
    const meta = TracksFeatureComponent.prototype.trackMeta.call(
      {},
      {
        id_track: 1,
        nombre_track: 'A',
        nombre_artista: 'B',
        popularity: 80,
        total_streams: null,
        engagement_score: null,
      },
    );
    expect(meta).toBe('Pop. 80');
    expect(meta).not.toMatch(/0 streams/);
  });

  it('trackMeta shows No disponible when no metrics exist', () => {
    const meta = TracksFeatureComponent.prototype.trackMeta.call(
      {},
      {
        id_track: 2,
        nombre_track: 'X',
        nombre_artista: 'Y',
        popularity: undefined as unknown as number,
        total_streams: null,
        engagement_score: null,
      },
    );
    expect(meta).toBe('No disponible');
  });

  it('trackMeta shows streams only when present', () => {
    const meta = TracksFeatureComponent.prototype.trackMeta.call(
      {},
      {
        id_track: 3,
        nombre_track: 'C',
        nombre_artista: 'D',
        popularity: 10,
        total_streams: 1500,
      },
    );
    expect(meta).toContain('streams');
    expect(meta).toContain('1');
  });
});
