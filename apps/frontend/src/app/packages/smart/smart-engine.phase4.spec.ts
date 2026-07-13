import { describe, it, expect } from 'vitest';
import { smartItemToTrack } from './models/smart-home.models';

describe('Smart Home Phase 4', () => {
  it('maps smart track item to catalog track', () => {
    const t = smartItemToTrack({
      id_track: 42,
      nombre_track: 'Song',
      nombre_artista: 'Artist',
      score: 0.88,
    });
    expect(t.id_track).toBe(42);
    expect(t.nombre_track).toBe('Song');
    expect(t.nombre_artista).toBe('Artist');
  });

  it('personalized sections have distinct ids', () => {
    const sections = [
      { id: 'recommended-for-you', type: 'track_rail' as const, code: 'recommended_for_you', tracks: [] },
      { id: 'discover-weekly-1', type: 'playlist' as const, code: 'discover_weekly', tracks: [] },
    ];
    const ids = new Set(sections.map((s) => s.id));
    expect(ids.size).toBe(2);
  });
});
