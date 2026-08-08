import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { MusicPlayerService } from './music-player.service';
import { CoverArtService } from './cover-art.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { TrackCoverService } from './track-cover.service';
import { StatsService } from '../../packages/analytics/services/stats.service';
import { ListenStatsService } from '../../packages/streaming/services/listen-stats.service';
import { PlayableTrack } from '../models/player.models';
import { QueueManager } from '../../playback-core/queue.manager';
import { PlaybackEngine } from '../../playback-core/playback.engine';
import type { PlaybackEngineHooks } from './player/player-playback.engine';

function sampleTrack(overrides: Partial<PlayableTrack> = {}): PlayableTrack {
  return {
    id: 42,
    title: 'Test Track',
    artist: 'Test Artist',
    durationMs: 180_000,
    audioUrl: '/assets/demo.mp3',
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
    startDemo: vi.fn((_url: string, trackId: number) => {
      engine.loadedId = trackId;
      return Promise.resolve(true);
    }),
    markLoaded: vi.fn((trackId: number) => { engine.loadedId = trackId; }),
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

describe('MusicPlayerService', () => {
  let svc: MusicPlayerService;
  let historyAdd: ReturnType<typeof vi.fn>;
  let mockEngine: ReturnType<typeof createMockEngine>;
  let engineHooks: PlaybackEngineHooks | null;

  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    historyAdd = vi.fn();
    mockEngine = createMockEngine();
    engineHooks = null;

    TestBed.configureTestingModule({
      providers: [
        MusicPlayerService,
        QueueManager,
        {
          provide: PlaybackEngine,
          useValue: {
            init: (hooks: PlaybackEngineHooks) => {
              engineHooks = hooks;
            },
            get instance() { return mockEngine; },
            isReady: true,
            destroy: vi.fn(),
          },
        },
        { provide: CoverArtService, useValue: { gradientFor: () => 'grad' } },
        { provide: HistoryService, useValue: { add: historyAdd, remove: vi.fn(), updateProgress: vi.fn(), completeCurrent: vi.fn(), pauseListenClock: vi.fn() } },
        {
          provide: TracksService,
          useValue: {
            getAudioSource: vi.fn(() =>
              of({
                track_id: 42,
                provider: 'youtube',
                status: 'not_found',
                youtube_video_id: null,
                playable_url: null,
              }),
            ),
            getCover: vi.fn(() => of({ status: 'ok', image_url: null })),
            listTracks: vi.fn(() => of({ total: 0, page: 1, limit: 24, items: [] })),
          },
        },
        {
          provide: TrackCoverService,
          useValue: { cover$: () => of('https://example.com/cover.jpg') },
        },
        {
          provide: StatsService,
          useValue: { getTopTracks: vi.fn(() => of([])) },
        },
        { provide: ListenStatsService, useValue: { tick: vi.fn() } },
      ],
    });

    svc = TestBed.inject(MusicPlayerService);
  });

  afterEach(() => {
    svc.stopPlayback();
    sessionStorage.clear();
    localStorage.clear();
  });

  describe('loadTrack (hotspot)', () => {
    it('sets currentTrack, duration, and resets currentTime', () => {
      const track = sampleTrack({ youtubeVideoId: 'abc' });
      svc.playTrack(track);
      expect(svc.currentTrack()?.id).toBe(track.id);
      expect(svc.currentTime()).toBe(0);
      expect(svc.duration()).toBe(180);
    });

    it('persists session to sessionStorage', async () => {
      vi.useFakeTimers();
      svc.playTrack(sampleTrack({ id: 7, title: 'Persisted', youtubeVideoId: 'abc' }));
      await vi.advanceTimersByTimeAsync(350);
      const raw = sessionStorage.getItem('vox:playback:session');
      expect(raw).toBeTruthy();
      const stored = JSON.parse(raw!) as { track: PlayableTrack };
      expect(stored.track.id).toBe(7);
      vi.useRealTimers();
    });

    it('records the track in listening history', () => {
      const track = sampleTrack({ youtubeVideoId: 'abc' });
      svc.playTrack(track);
      expect(historyAdd).toHaveBeenCalledWith({
        id_track: track.id,
        nombre_track: track.title,
        nombre_artista: track.artist,
      });
    });

    it('resolves YouTube playback when youtubeVideoId is present', () => {
      svc.playTrack(sampleTrack({ youtubeVideoId: 'dQw4w9WgXcQ' }));
      expect(svc.audioMode()).toBe('youtube');
      expect(mockEngine.startYoutube).toHaveBeenCalledWith('dQw4w9WgXcQ', true);
      expect(svc.status()).toBe('playing');
      expect(svc.resolvePhase()).toBe('playing');
    });

    it('falls back to unavailable when no playable source exists (never generic demo)', () => {
      svc.playTrack(sampleTrack({ audioUrl: '/assets/audio/demo-01.wav' }));
      expect(svc.resolvePhase()).toBe('unavailable');
      expect(svc.status()).toBe('error');
      expect(svc.audioMode()).toBe('loading');
      expect(mockEngine.startDemo).not.toHaveBeenCalled();
    });

    it('auto-skips to next after failPlayback message (~1200ms)', async () => {
      vi.useFakeTimers();
      const a = sampleTrack({ id: 1, title: 'A', audioUrl: '/assets/audio/demo-01.wav' });
      const b = sampleTrack({ id: 2, title: 'B', youtubeVideoId: 'b' });
      svc.setQueue([a, b], 0);
      expect(svc.status()).toBe('error');
      expect(svc.playbackError()).toBeTruthy();
      await vi.advanceTimersByTimeAsync(1200);
      expect(svc.currentTrack()?.id).toBe(2);
      vi.useRealTimers();
    });
  });

  describe('listen progress wiring', () => {
    it('calls history.updateProgress from onTick while playing', () => {
      const history = TestBed.inject(HistoryService) as unknown as {
        updateProgress: ReturnType<typeof vi.fn>;
      };
      svc.playTrack(sampleTrack({ youtubeVideoId: 'abc' }));
      mockEngine.getCurrentTime.mockReturnValue(12);
      mockEngine._tick();
      expect(history.updateProgress).toHaveBeenCalledWith(12, expect.any(Number));
    });

    it('pause and seek pause the listen clock so seeks do not inflate listen time', () => {
      const history = TestBed.inject(HistoryService) as unknown as {
        pauseListenClock: ReturnType<typeof vi.fn>;
        completeCurrent: ReturnType<typeof vi.fn>;
      };
      svc.playTrack(sampleTrack({ youtubeVideoId: 'abc' }));
      svc.pause();
      expect(history.pauseListenClock).toHaveBeenCalled();
      history.pauseListenClock.mockClear();
      svc.seek(30);
      expect(history.pauseListenClock).toHaveBeenCalled();
    });

    it('stopPlayback and track change close the listen session via completeCurrent', () => {
      const history = TestBed.inject(HistoryService) as unknown as {
        completeCurrent: ReturnType<typeof vi.fn>;
      };
      svc.playTrack(sampleTrack({ id: 1, youtubeVideoId: 'a' }));
      history.completeCurrent.mockClear();
      svc.playTrack(sampleTrack({ id: 2, youtubeVideoId: 'b' }));
      expect(history.completeCurrent).toHaveBeenCalled();
      history.completeCurrent.mockClear();
      svc.stopPlayback();
      expect(history.completeCurrent).toHaveBeenCalled();
    });
  });

  describe('transport controls', () => {
    it('pause and resume toggle status', () => {
      svc.playTrack(sampleTrack({ youtubeVideoId: 'abc' }));
      svc.pause();
      expect(svc.status()).toBe('paused');
      svc.resume();
      expect(svc.status()).toBe('playing');
    });

    it('next advances queue', () => {
      const a = sampleTrack({ id: 1, title: 'A', youtubeVideoId: 'a' });
      const b = sampleTrack({ id: 2, title: 'B', youtubeVideoId: 'b' });
      svc.setQueue([a, b], 0);
      expect(svc.currentTrack()?.id).toBe(1);
      svc.next();
      expect(svc.currentTrack()?.id).toBe(2);
    });

    it('previous uses playback history after seek reset window', () => {
      const a = sampleTrack({ id: 1, title: 'A', youtubeVideoId: 'a' });
      const b = sampleTrack({ id: 2, title: 'B', youtubeVideoId: 'b' });
      svc.setQueue([a, b], 0);
      svc.next();
      svc.previous();
      expect(svc.currentTrack()?.id).toBe(1);
    });

    it('cycleRepeat cycles off → all → one', () => {
      expect(svc.repeatMode()).toBe('off');
      svc.cycleRepeat();
      expect(svc.repeatMode()).toBe('all');
      svc.cycleRepeat();
      expect(svc.repeatMode()).toBe('one');
    });

    it('toggleMute persists preference', () => {
      svc.toggleMute();
      expect(svc.muted()).toBe(true);
      const prefs = JSON.parse(localStorage.getItem('vox:playback:prefs')!);
      expect(prefs.muted).toBe(true);
    });

    it('addToQueue appends without playing', () => {
      svc.playTrack(sampleTrack({ id: 1, youtubeVideoId: 'a' }));
      const added = svc.addToQueue(sampleTrack({ id: 99, title: 'Queued' }));
      expect(added).toBe(true);
      expect(svc.queue().length).toBe(2);
      expect(svc.currentTrack()?.id).toBe(1);
    });
  });

  describe('repeat-one via real onEnded callback', () => {
    it('completes once, opens a new history session, and resumes the same track', () => {
      const history = TestBed.inject(HistoryService) as unknown as {
        completeCurrent: ReturnType<typeof vi.fn>;
        add: ReturnType<typeof vi.fn>;
      };
      expect(engineHooks?.onEnded).toEqual(expect.any(Function));

      const track = sampleTrack({ id: 9, title: 'Loop Me', artist: 'Looper', youtubeVideoId: 'loopVid' });
      svc.setRepeatMode('one');
      svc.playTrack(track);

      history.completeCurrent.mockClear();
      historyAdd.mockClear();
      mockEngine.seek.mockClear();
      mockEngine.playYoutube.mockClear();

      // Invoke the productive callback registered by MusicPlayerService constructor.
      engineHooks!.onEnded!();

      expect(history.completeCurrent).toHaveBeenCalledTimes(1);
      expect(historyAdd).toHaveBeenCalledTimes(1);
      expect(historyAdd).toHaveBeenCalledWith({
        id_track: track.id,
        nombre_track: track.title,
        nombre_artista: track.artist,
      });
      expect(mockEngine.seek).toHaveBeenCalledWith(0);
      expect(svc.currentTrack()?.id).toBe(track.id);
      expect(svc.status()).toBe('playing');
      // New session via history.add — must not reuse prior identity by replaying loadTrack.
      expect(svc.currentTrack()?.youtubeVideoId).toBe('loopVid');
    });
  });
});
