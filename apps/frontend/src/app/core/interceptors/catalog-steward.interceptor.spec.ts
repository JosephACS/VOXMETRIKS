import { describe, expect, it } from 'vitest';

import { isCatalogStewardMutation } from './catalog-steward.interceptor';

describe('catalogStewardInterceptor route policy', () => {
  it('allows authenticated listener playback operations', () => {
    expect(
      isCatalogStewardMutation(
        'http://127.0.0.1:8000/api/v1/tracks/music-search/adopt',
        'POST',
      ),
    ).toBe(false);
    expect(
      isCatalogStewardMutation('/api/v1/tracks/89741/audio-source/failure', 'POST'),
    ).toBe(false);
  });

  it('continues blocking manual catalog mutations for listeners', () => {
    expect(isCatalogStewardMutation('/api/v1/tracks', 'POST')).toBe(true);
    expect(isCatalogStewardMutation('/api/v1/tracks/42', 'PUT')).toBe(true);
    expect(isCatalogStewardMutation('/api/v1/artists/7', 'DELETE')).toBe(true);
    expect(isCatalogStewardMutation('/api/v1/genres/3', 'PATCH')).toBe(true);
  });

  it('never treats reads as catalog mutations', () => {
    expect(isCatalogStewardMutation('/api/v1/tracks/music-search', 'GET')).toBe(false);
  });
});
