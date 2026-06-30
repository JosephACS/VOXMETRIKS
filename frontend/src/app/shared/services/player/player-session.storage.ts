import { PlayableTrack } from '../../models/player.models';

const VOLUME_KEY = 'voxmetrik_volume';
const TRACK_KEY = 'voxmetrik_last_track';

export function readStoredVolume(): number {
  const v = parseFloat(localStorage.getItem(VOLUME_KEY) ?? '0.85');
  return Number.isFinite(v) ? v : 0.85;
}

export function storeVolume(vol: number): void {
  localStorage.setItem(VOLUME_KEY, String(vol));
}

export function persistCurrentTrack(track: PlayableTrack): void {
  sessionStorage.setItem(TRACK_KEY, JSON.stringify(track));
}

export function clearPersistedTrack(): void {
  sessionStorage.removeItem(TRACK_KEY);
}

export function restorePersistedTrack(): PlayableTrack | null {
  try {
    const raw = sessionStorage.getItem(TRACK_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as PlayableTrack;
  } catch {
    return null;
  }
}
