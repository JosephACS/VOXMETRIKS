import { TestBed } from '@angular/core/testing';
import { of, Observable } from 'rxjs';
import { PlayerController } from './player.controller';
import { PlaybackStore } from './playback.store';
import { FavoritesStore } from './favorites.store';
import { QueueManager } from './queue.manager';
import { MusicPlayerService } from '../shared/services/music-player.service';
import { PlaybackEngine } from './playback.engine';
import { CoverArtService } from '../shared/services/cover-art.service';
import { HistoryService } from '../packages/streaming/services/history.service';
import { TracksService } from '../packages/streaming/services/tracks.service';
import { TrackCoverService } from '../shared/services/track-cover.service';
import { StatsService } from '../packages/analytics/services/stats.service';
import { ListenStatsService } from '../packages/streaming/services/listen-stats.service';
import { FavoritesService } from '../packages/streaming/services/favorites.service';
import { PlayableTrack } from '../shared/models/player.models';

function sampleTrack(overrides: Partial<PlayableTrack> = {}): PlayableTrack {
  return {
    id: 42,
    title: 'Test Track',
    artist: 'Test Artist',
    durationMs: 180_000,
    audioUrl: '/assets/audio/demo-01.wav',
    coverGradient: 'linear-gradient(135deg, #111, #333)',
    ...overrides,
  };
}

function createMockEngine() {
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
    startTick: vi.fn(),
    destroy: vi.fn(),
  };
  return engine;
}

describe('Playback Spotify UX Phase 1', () => {
  let controller: PlayerController;
  let store: PlaybackStore;
  let favStore: FavoritesStore;
  let favSvc: {
    favoriteIds$: Observable<Set<number>>;
    toggle: ReturnType<typeof vi.fn>;
    add: ReturnType<typeof vi.fn>;
    remove: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    localStorage.setItem('vox:playback:prefs', JSON.stringify({
      volume: 0.85, muted: false, shuffle: false, repeatMode: 'off', autoplay: false,
    }));
    favSvc = {
      favoriteIds$: of(new Set<number>()),
      toggle: vi.fn(() => of({ favorited: true, track_id: 7 })),
      add: vi.fn(() => of({ favorited: true, track_id: 7 })),
      remove: vi.fn(() => of({ removed: true, track_id: 7 })),
    };

    TestBed.configureTestingModule({
      providers: [
        MusicPlayerService,
        PlayerController,
        PlaybackStore,
        FavoritesStore,
        QueueManager,
        {
          provide: PlaybackEngine,
          useValue: {
            init: () => undefined,
            get instance() { return createMockEngine(); },
            isReady: true,
            destroy: vi.fn(),
          },
        },
        { provide: CoverArtService, useValue: { gradientFor: () => 'grad' } },
        { provide: HistoryService, useValue: { add: vi.fn(), remove: vi.fn(), updateProgress: vi.fn(), completeCurrent: vi.fn(), pauseListenClock: vi.fn() } },
        {
          provide: TracksService,
          useValue: {
            getAudioSource: () => of({ status: 'not_found', youtube_video_id: null }),
            listTracks: () => of({ items: [], total: 0 }),
          },
        },
        { provide: TrackCoverService, useValue: { cover$: () => of(null) } },
        { provide: StatsService, useValue: { getTopTracks: () => of([]) } },
        { provide: ListenStatsService, useValue: { tick: vi.fn(), reload: vi.fn(), minutesToday: () => 0 } },
        {
          provide: FavoritesService,
          useValue: {
            favoriteIds$: favSvc.favoriteIds$,
            toggle: favSvc.toggle,
            add: favSvc.add,
            remove: favSvc.remove,
            loadFavorites: () => of([]),
            refreshIds: vi.fn(),
          },
        },
      ],
    });

    controller = TestBed.inject(PlayerController);
    store = TestBed.inject(PlaybackStore);
    favStore = TestBed.inject(FavoritesStore);
  });

  it('adds favorite without starting playback', () => {
    favStore.toggle(7).subscribe();
    expect(favSvc.toggle).toHaveBeenCalledWith(7);
    expect(store.currentTrack()).toBeNull();
    expect(store.isPlaying()).toBe(false);
  });

  it('toggle favorite delegates to favorites service', () => {
    favStore.toggle(7).subscribe();
    expect(favSvc.toggle).toHaveBeenCalledWith(7);
    expect(store.currentTrack()).toBeNull();
  });

  it('adds track to global queue without playing', () => {
    controller.playTrack(sampleTrack({ id: 1 }));
    const queued = sampleTrack({ id: 99, title: 'Queued' });
    const added = controller.addToQueue(queued);
    expect(added).toBe(true);
    expect(store.queue().some((t) => t.id === 99)).toBe(true);
    expect(store.currentTrack()?.id).toBe(1);
  });

  it('plays track immediately from card intent', () => {
    const track = sampleTrack({ id: 5, title: 'Play Now' });
    controller.playTrack(track);
    expect(store.currentTrack()?.id).toBe(5);
  });

  it('inserts play-next without replacing current track', () => {
    controller.playTrack(sampleTrack({ id: 1 }));
    controller.playNextInQueue(sampleTrack({ id: 2, title: 'Next' }));
    expect(store.currentTrack()?.id).toBe(1);
    expect(store.queue()[1]?.id).toBe(2);
  });

  it('keeps queue in global store across controller calls', () => {
    const q = [sampleTrack({ id: 1 }), sampleTrack({ id: 2 }), sampleTrack({ id: 3 })];
    controller.setQueue(q, 0);
    expect(store.queue().length).toBe(3);
    controller.next();
    expect(store.currentTrack()?.id).toBe(2);
  });

  it('playback store exposes transport state for persistent player', () => {
    controller.playTrack(sampleTrack());
    expect(store.hasCurrentTrack()).toBe(true);
    expect(store.queue()).toBeTruthy();
    controller.pause();
    expect(store.isPlaying()).toBe(false);
  });
});
