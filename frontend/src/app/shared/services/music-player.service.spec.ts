import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { MusicPlayerService } from './music-player.service';
import { CoverArtService } from './cover-art.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { YoutubeEngineService } from './youtube-engine.service';
import { TrackCoverService } from './track-cover.service';
import { StatsService } from '../../packages/analytics/services/stats.service';
import { PlayableTrack } from '../models/player.models';

/** Minimal playable track for loadTrack hotspot tests. */
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

describe('MusicPlayerService.loadTrack (hotspot)', () => {
  let svc: MusicPlayerService;
  let historyAdd: ReturnType<typeof vi.fn>;
  let ytLoad: ReturnType<typeof vi.fn>;
  let ytStop: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();

    historyAdd = vi.fn();
    ytLoad = vi.fn();
    ytStop = vi.fn();

    TestBed.configureTestingModule({
      providers: [
        MusicPlayerService,
        { provide: CoverArtService, useValue: { gradientFor: () => 'grad' } },
        { provide: HistoryService, useValue: { add: historyAdd, remove: vi.fn() } },
        {
          provide: TracksService,
          useValue: {
            getAudioSource: vi.fn(() => of({ status: 'ok', youtube_video_id: null })),
            getCover: vi.fn(() => of({ status: 'ok', image_url: null })),
            listTracks: vi.fn(() => of({ total: 0, page: 1, limit: 24, items: [] })),
          },
        },
        {
          provide: YoutubeEngineService,
          useValue: {
            load: ytLoad,
            stop: ytStop,
            play: vi.fn(),
            pause: vi.fn(),
            seekTo: vi.fn(),
            setVolume: vi.fn(),
            getCurrentTime: () => 0,
            getDuration: () => 0,
            onPlay: null,
            onPause: null,
            onEnded: null,
            onError: null,
          },
        },
        {
          provide: TrackCoverService,
          useValue: { cover$: () => of('https://example.com/cover.jpg') },
        },
        {
          provide: StatsService,
          useValue: {
            getTopTracks: vi.fn(() => of([])),
          },
        },
      ],
    });

    svc = TestBed.inject(MusicPlayerService);
  });

  afterEach(() => {
    svc.stopPlayback();
    sessionStorage.clear();
    localStorage.clear();
  });

  it('sets currentTrack, duration, and resets currentTime', () => {
    const track = sampleTrack();
    svc.playTrack(track);

    expect(svc.currentTrack()).toEqual(track);
    expect(svc.currentTime()).toBe(0);
    expect(svc.duration()).toBe(180);
  });

  it('persists the track to sessionStorage', () => {
    const track = sampleTrack({ id: 7, title: 'Persisted' });
    svc.playTrack(track);

    const raw = sessionStorage.getItem('voxmetrik_last_track');
    expect(raw).toBeTruthy();
    const stored = JSON.parse(raw!) as PlayableTrack;
    expect(stored.id).toBe(7);
    expect(stored.title).toBe('Persisted');
  });

  it('records the track in listening history', () => {
    const track = sampleTrack();
    svc.playTrack(track);

    expect(historyAdd).toHaveBeenCalledWith({
      id_track: track.id,
      nombre_track: track.title,
      nombre_artista: track.artist,
    });
  });

  it('resolves YouTube playback when youtubeVideoId is present', () => {
    const track = sampleTrack({ youtubeVideoId: 'dQw4w9WgXcQ' });
    svc.playTrack(track);

    expect(svc.audioMode()).toBe('youtube');
    expect(ytLoad).toHaveBeenCalledWith('dQw4w9WgXcQ', true);
    expect(svc.isPlaying()).toBe(true);
  });

  it('falls back to demo mode when no YouTube id is available', () => {
    const track = sampleTrack();
    svc.playTrack(track);

    expect(svc.audioMode()).toBe('demo');
    expect(ytStop).toHaveBeenCalled();
  });

  it('ignores stale cover updates after a rapid track switch', () => {
    const first = sampleTrack({ id: 1, title: 'First' });
    const second = sampleTrack({ id: 2, title: 'Second' });

    svc.playTrack(first);
    svc.playTrack(second);

    expect(svc.currentTrack()?.id).toBe(2);
    expect(svc.currentCover()).toBe('https://example.com/cover.jpg');
  });
});
