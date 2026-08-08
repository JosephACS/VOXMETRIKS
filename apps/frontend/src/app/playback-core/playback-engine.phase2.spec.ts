import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { PlayerController } from './player.controller';
import { PlaybackStore } from './playback.store';
import { QueueManager } from './queue.manager';
import { MusicPlayerService } from '../shared/services/music-player.service';
import { PlaybackEngine } from './playback.engine';
import { CoverArtService } from '../shared/services/cover-art.service';
import { HistoryService } from '../packages/streaming/services/history.service';
import { TracksService } from '../packages/streaming/services/tracks.service';
import { TrackCoverService } from '../shared/services/track-cover.service';
import { StatsService } from '../packages/analytics/services/stats.service';
import { ListenStatsService } from '../packages/streaming/services/listen-stats.service';
import { PlayableTrack } from '../shared/models/player.models';
import { nextIndex } from './playback-history';
import {
  persistPlaybackSession,
  readPlaybackPrefs,
  restorePlaybackSession,
} from '../shared/services/player/player-session.storage';

function sampleTrack(overrides: Partial<PlayableTrack> = {}): PlayableTrack {
  return {
    id: 42,
    title: 'Test Track',
    artist: 'Test Artist',
    durationMs: 180_000,
    audioUrl: '',
    youtubeVideoId: 'phase2TestVideo',
    coverGradient: 'linear-gradient(135deg, #111, #333)',
    ...overrides,
  };
}

function createMockEngine() {
  let tickFn: (() => void) | null = null;
  const engine = {
    isYoutube: false,
    loadedId: null as number | null,
    setVolume: vi.fn(),
    primeDemo: vi.fn(),
    startYoutube: vi.fn(),
    startDemo: vi.fn((_url: string, trackId: number, autoplay?: boolean) => {
      engine.loadedId = trackId;
      return Promise.resolve(autoplay !== false);
    }),
    markLoaded: vi.fn((trackId: number, youtube?: boolean) => {
      engine.loadedId = trackId;
      engine.isYoutube = !!youtube;
    }),
    pause: vi.fn(),
    playDemo: vi.fn(() => Promise.resolve(true)),
    playYoutube: vi.fn(),
    seek: vi.fn((s: number) => s),
    getCurrentTime: vi.fn(() => 0),
    getDuration: vi.fn((_f: number) => 180),
    stopAll: vi.fn(),
    startTick: vi.fn((fn: () => void) => { tickFn = fn; }),
    destroy: vi.fn(),
    _tick: () => tickFn?.(),
  };
  return engine;
}

describe('Playback Engine Phase 2', () => {
  let controller: PlayerController;
  let store: PlaybackStore;
  let svc: MusicPlayerService;
  let mockEngine: ReturnType<typeof createMockEngine>;

  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    localStorage.setItem('vox:playback:prefs', JSON.stringify({
      volume: 0.85, muted: false, shuffle: false, repeatMode: 'off', autoplay: false,
    }));
    mockEngine = createMockEngine();

    TestBed.configureTestingModule({
      providers: [
        MusicPlayerService,
        PlayerController,
        PlaybackStore,
        QueueManager,
        {
          provide: PlaybackEngine,
          useValue: {
            init: () => undefined,
            get instance() { return mockEngine; },
            isReady: true,
            destroy: vi.fn(),
          },
        },
        { provide: CoverArtService, useValue: { gradientFor: () => 'grad' } },
        { provide: HistoryService, useValue: { add: vi.fn(), remove: vi.fn(), updateProgress: vi.fn(), completeCurrent: vi.fn(), pauseListenClock: vi.fn() } },
        {
          provide: TracksService,
          useValue: {
            getAudioSource: vi.fn((id: number) =>
              of({
                track_id: id,
                provider: 'youtube',
                status: 'ok',
                youtube_video_id: 'phase2TestVideo',
                playable_url: null,
              }),
            ),
            getCover: vi.fn(() => of({ status: 'ok', image_url: null })),
            listTracks: vi.fn(() => of({ total: 0, page: 1, limit: 24, items: [] })),
          },
        },
        { provide: TrackCoverService, useValue: { cover$: () => of(null) } },
        { provide: StatsService, useValue: { getTopTracks: vi.fn(() => of([])) } },
        { provide: ListenStatsService, useValue: { tick: vi.fn() } },
      ],
    });

    controller = TestBed.inject(PlayerController);
    store = TestBed.inject(PlaybackStore);
    svc = TestBed.inject(MusicPlayerService);
  });

  afterEach(() => {
    svc.stopPlayback();
    sessionStorage.clear();
    localStorage.clear();
  });

  it('1. play/pause toggles status', async () => {
    controller.playTrack(sampleTrack());
    await Promise.resolve();
    expect(store.status()).toBe('playing');
    controller.pause();
    expect(store.status()).toBe('paused');
    controller.resume();
    expect(store.status()).toBe('playing');
  });

  it('2. next plays the following track in queue', () => {
    const a = sampleTrack({ id: 1, title: 'A' });
    const b = sampleTrack({ id: 2, title: 'B' });
    controller.setQueue([a, b], 0);
    expect(store.currentTrack()?.id).toBe(1);
    controller.next();
    expect(store.currentTrack()?.id).toBe(2);
  });

  it('3. previous returns to playback history', () => {
    const a = sampleTrack({ id: 1, title: 'A' });
    const b = sampleTrack({ id: 2, title: 'B' });
    controller.setQueue([a, b], 0);
    controller.next();
    controller.previous();
    expect(store.currentTrack()?.id).toBe(1);
    expect(store.playHistory().length).toBe(0);
  });

  it('4. shuffle changes next index', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.99);
    const idx = nextIndex(5, 0, true, 'off');
    expect(idx).not.toBe(0);
    vi.mocked(Math.random).mockRestore();
  });

  it('5. repeat one keeps same track on ended', () => {
    const t = sampleTrack({ id: 1 });
    controller.setQueue([t], 0);
    controller.setRepeatMode('one');
    expect(store.repeatMode()).toBe('one');
    controller.next();
    expect(store.currentTrack()?.id).toBe(1);
  });

  it('6. repeat all wraps queue at end', () => {
    const a = sampleTrack({ id: 1 });
    const b = sampleTrack({ id: 2 });
    const c = sampleTrack({ id: 3 });
    controller.setQueue([a, b, c], 2);
    controller.setRepeatMode('all');
    controller.next();
    expect(store.currentTrack()?.id).toBe(1);
  });

  it('7. volume persists to localStorage', () => {
    controller.setVolume(0.42);
    const prefs = readPlaybackPrefs();
    expect(prefs.volume).toBe(0.42);
  });

  it('8. queue persists in sessionStorage', async () => {
    vi.useFakeTimers();
    const a = sampleTrack({ id: 1 });
    const b = sampleTrack({ id: 2 });
    controller.setQueue([a, b], 0);
    await vi.advanceTimersByTimeAsync(350);
    const session = restorePlaybackSession();
    expect(session?.queue.length).toBe(2);
    expect(session?.queueIndex).toBe(0);
    vi.useRealTimers();
  });

  it('9. player state survives simulated navigation (singleton)', async () => {
    const track = sampleTrack({ id: 99, title: 'Persistent' });
    controller.playTrack(track);
    await Promise.resolve();
    const trackBefore = store.currentTrack()?.id;
    const store2 = TestBed.inject(PlaybackStore);
    expect(store2.currentTrack()?.id).toBe(trackBefore);
    expect(store2.status()).toBe('playing');
  });

  it('10. audio error does not block app — sets error then can retry', async () => {
    const tracksApi = TestBed.inject(TracksService);
    const getAudio = vi.mocked(tracksApi.getAudioSource);
    getAudio.mockReturnValueOnce(
      of({
        track_id: 55,
        provider: 'none',
        status: 'not_found',
        youtube_video_id: null,
        playable_url: null,
      }) as never,
    );
    getAudio.mockReturnValue(
      of({
        track_id: 55,
        provider: 'youtube',
        status: 'ok',
        youtube_video_id: 'retryVideo',
        playable_url: null,
      }) as never,
    );

    controller.playTrack(sampleTrack({ id: 55, youtubeVideoId: '', audioUrl: '' }));
    await Promise.resolve();
    expect(store.status()).toBe('error');
    expect(store.playbackError()).toBeTruthy();

    controller.retryCurrent();
    await Promise.resolve();
    expect(store.playbackError()).toBeNull();
    expect(store.status()).toBe('playing');
  });
});

describe('player-session.storage phase2', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it('restores session paused without autoplay', () => {
    const track = sampleTrack({ id: 5 });
    persistPlaybackSession({
      track,
      queue: [track],
      queueIndex: 0,
      currentTime: 42,
      playbackHistory: [],
    });
    const restored = restorePlaybackSession();
    expect(restored?.track?.id).toBe(5);
    expect(restored?.currentTime).toBe(42);
  });

  it('persists shuffle and repeat prefs', () => {
    localStorage.setItem('vox:playback:prefs', JSON.stringify({
      volume: 0.5, muted: true, shuffle: true, repeatMode: 'all', autoplay: false,
    }));
    const prefs = readPlaybackPrefs();
    expect(prefs.shuffle).toBe(true);
    expect(prefs.repeatMode).toBe('all');
    expect(prefs.muted).toBe(true);
  });
});
