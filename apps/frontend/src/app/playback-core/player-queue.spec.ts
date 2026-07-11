import { describe, it, expect, beforeEach } from 'vitest';
import { PlayerQueue } from '../shared/services/player/player-queue';
import { PlayableTrack } from '../shared/models/player.models';

function track(id: number): PlayableTrack {
  return {
    id,
    title: `T${id}`,
    artist: 'A',
    audioUrl: '/a.wav',
    coverGradient: 'g',
  };
}

describe('PlayerQueue phase2', () => {
  let q: PlayerQueue;

  beforeEach(() => {
    q = new PlayerQueue();
    q.setAll([track(1), track(2), track(3)], 0);
  });

  it('advance with repeat off stops at last', () => {
    q.jumpTo(2);
    expect(q.advance(false, 'off')).toBeNull();
  });

  it('advance with repeat all wraps', () => {
    q.jumpTo(2);
    expect(q.advance(false, 'all')?.id).toBe(1);
  });

  it('move reorders and keeps current index coherent', () => {
    q.jumpTo(1);
    expect(q.move(2, 0)).toBe(true);
    expect(q.items[0].id).toBe(3);
  });

  it('removeAt adjusts current index', () => {
    q.jumpTo(1);
    q.removeAt(0);
    expect(q.current?.id).toBe(2);
  });
});
