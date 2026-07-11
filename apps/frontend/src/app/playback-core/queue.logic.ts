import { RepeatMode } from '../shared/models/player.models';
import { hasNextTrack, nextIndex } from './playback-history';

export { hasNextTrack, nextIndex, cycleRepeatMode } from './playback-history';
export type { PlaybackHistoryStack } from './playback-history';

/** Re-export queue navigation helpers used by PlayerQueue. */
export function computeHasNext(
  queueLength: number,
  index: number,
  shuffle: boolean,
  repeatMode: RepeatMode,
): boolean {
  return hasNextTrack(queueLength, index, shuffle, repeatMode);
}

export function computeNextIndex(
  queueLength: number,
  index: number,
  shuffle: boolean,
  repeatMode: RepeatMode,
): number | null {
  return nextIndex(queueLength, index, shuffle, repeatMode);
}
