import { describe, it, expect } from 'vitest';
import {
  PlaybackHistoryStack,
  cycleRepeatMode,
  hasNextTrack,
  nextIndex,
} from './playback-history';
import { PlayableTrack } from '../shared/models/player.models';

function track(id: number): PlayableTrack {
  return {
    id,
    title: `Track ${id}`,
    artist: 'Artist',
    audioUrl: `/assets/audio/demo-0${(id % 8) + 1}.wav`,
    coverGradient: 'linear-gradient(#111,#333)',
  };
}

describe('PlaybackHistoryStack', () => {
  it('pushes and pops tracks', () => {
    const h = new PlaybackHistoryStack();
    h.push(track(1));
    h.push(track(2));
    expect(h.pop()?.id).toBe(2);
    expect(h.pop()?.id).toBe(1);
    expect(h.pop()).toBeNull();
  });

  it('skips duplicate consecutive pushes', () => {
    const h = new PlaybackHistoryStack();
    h.push(track(1));
    h.push(track(1));
    expect(h.size).toBe(1);
  });
});

describe('cycleRepeatMode', () => {
  it('cycles off → all → one → off', () => {
    expect(cycleRepeatMode('off')).toBe('all');
    expect(cycleRepeatMode('all')).toBe('one');
    expect(cycleRepeatMode('one')).toBe('off');
  });
});

describe('queue navigation', () => {
  it('hasNext respects repeat off at end', () => {
    expect(hasNextTrack(3, 2, false, 'off')).toBe(false);
    expect(hasNextTrack(3, 1, false, 'off')).toBe(true);
  });

  it('hasNext wraps with repeat all', () => {
    expect(hasNextTrack(3, 2, false, 'all')).toBe(true);
  });

  it('nextIndex returns null at end when repeat off', () => {
    expect(nextIndex(3, 2, false, 'off')).toBeNull();
    expect(nextIndex(3, 2, false, 'all')).toBe(0);
  });

  it('nextIndex stays on repeat one', () => {
    expect(nextIndex(3, 1, false, 'one')).toBe(1);
  });
});
