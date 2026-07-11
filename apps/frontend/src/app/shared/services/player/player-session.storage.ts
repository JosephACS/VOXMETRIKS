import { PlayableTrack, RepeatMode } from '../../models/player.models';

const PREFS_KEY = 'vox:playback:prefs';
const SESSION_KEY = 'vox:playback:session';
/** Legacy keys — migrated on read. */
const LEGACY_VOLUME_KEY = 'voxmetrik_volume';
const LEGACY_TRACK_KEY = 'voxmetrik_last_track';

export interface PlaybackPrefs {
  volume: number;
  muted: boolean;
  shuffle: boolean;
  repeatMode: RepeatMode;
  autoplay: boolean;
}

export interface PersistedPlaybackSession {
  track: PlayableTrack | null;
  queue: PlayableTrack[];
  queueIndex: number;
  currentTime: number;
  playbackHistory: PlayableTrack[];
}

const DEFAULT_PREFS: PlaybackPrefs = {
  volume: 0.85,
  muted: false,
  shuffle: false,
  repeatMode: 'off',
  autoplay: true,
};

export function readPlaybackPrefs(): PlaybackPrefs {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (raw) {
      const p = JSON.parse(raw) as Partial<PlaybackPrefs>;
      return {
        volume: clampVolume(p.volume ?? readLegacyVolume()),
        muted: p.muted ?? false,
        shuffle: p.shuffle ?? false,
        repeatMode: p.repeatMode ?? 'off',
        autoplay: p.autoplay ?? true,
      };
    }
  } catch { /* ignore */ }
  return { ...DEFAULT_PREFS, volume: readLegacyVolume() };
}

export function storePlaybackPrefs(prefs: PlaybackPrefs): void {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  localStorage.setItem(LEGACY_VOLUME_KEY, String(prefs.volume));
}

export function readLegacyVolume(): number {
  const v = parseFloat(localStorage.getItem(LEGACY_VOLUME_KEY) ?? '0.85');
  return clampVolume(v);
}

export function storeVolume(vol: number): void {
  const prefs = readPlaybackPrefs();
  prefs.volume = clampVolume(vol);
  storePlaybackPrefs(prefs);
}

function clampVolume(v: number): number {
  return Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0.85;
}

export function persistPlaybackSession(session: PersistedPlaybackSession): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  if (session.track) {
    sessionStorage.setItem(LEGACY_TRACK_KEY, JSON.stringify(session.track));
  }
}

export function restorePlaybackSession(): PersistedPlaybackSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw) as PersistedPlaybackSession;
    const legacy = sessionStorage.getItem(LEGACY_TRACK_KEY);
    if (!legacy) return null;
    const track = JSON.parse(legacy) as PlayableTrack;
    return {
      track,
      queue: [track],
      queueIndex: 0,
      currentTime: 0,
      playbackHistory: [],
    };
  } catch {
    return null;
  }
}

export function clearPersistedSession(): void {
  sessionStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(LEGACY_TRACK_KEY);
}

/** @deprecated use persistPlaybackSession */
export function persistCurrentTrack(track: PlayableTrack): void {
  sessionStorage.setItem(LEGACY_TRACK_KEY, JSON.stringify(track));
}

/** @deprecated use clearPersistedSession */
export function clearPersistedTrack(): void {
  clearPersistedSession();
}

/** @deprecated use restorePlaybackSession */
export function restorePersistedTrack(): PlayableTrack | null {
  return restorePlaybackSession()?.track ?? null;
}

/** @deprecated */
export function readStoredVolume(): number {
  return readPlaybackPrefs().volume;
}
