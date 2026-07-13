import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { AudioResolver } from './audio.resolver';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { PlayableTrack } from '../../shared/models/player.models';

function track(id = 1): PlayableTrack {
  return {
    id,
    title: 'Song',
    artist: 'Artist',
    audioUrl: '',
    coverGradient: 'g',
  };
}

describe('AudioResolver Phase 3', () => {
  let resolver: AudioResolver;
  let getAudioSource: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    getAudioSource = vi.fn();
    TestBed.configureTestingModule({
      providers: [
        AudioResolver,
        { provide: TracksService, useValue: { getAudioSource } },
        { provide: HistoryService, useValue: { remove: vi.fn() } },
      ],
    });
    resolver = TestBed.inject(AudioResolver);
  });

  it('1. uses cached YouTube id on track without API call', () => {
    const onYoutube = vi.fn();
    resolver.resolvePlayableSource(
      { ...track(), youtubeVideoId: 'cached-id' },
      {
        onResolving: vi.fn(),
        onYoutube,
        onStream: vi.fn(),
        onPreview: vi.fn(),
        onNotFound: vi.fn(),
        onTrackUpdated: vi.fn(),
        isStale: () => false,
      },
    );
    expect(onYoutube).toHaveBeenCalledWith('cached-id');
    expect(getAudioSource).not.toHaveBeenCalled();
  });

  it('2. resolves uncached track via API (sync wait)', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'youtube',
        youtube_video_id: 'new-id',
        status: 'ok',
      }),
    );
    const onYoutube = vi.fn();
    const onPreview = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube,
      onStream: vi.fn(),
      onPreview,
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(getAudioSource).toHaveBeenCalledWith(1, { asyncResolve: false });
    expect(onYoutube).toHaveBeenCalledWith('new-id');
    expect(onPreview).not.toHaveBeenCalled();
  });

  it('3. falls back to stream when Audius resolves', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'audius',
        source_ref: '55',
        playable_url: 'https://api.audius.co/v1/tracks/55/stream',
        status: 'ok',
      }),
    );
    const onStream = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube: vi.fn(),
      onStream,
      onPreview: vi.fn(),
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onStream).toHaveBeenCalledWith('https://api.audius.co/v1/tracks/55/stream');
  });

  it('4. not_found triggers onNotFound (never generic demo)', () => {
    getAudioSource.mockReturnValue(
      of({ track_id: 1, provider: 'youtube', status: 'not_found' }),
    );
    const onNotFound = vi.fn();
    const onPreview = vi.fn();
    resolver.resolvePlayableSource(
      { ...track(), audioUrl: '/assets/audio/demo-01.wav' },
      {
        onResolving: vi.fn(),
        onYoutube: vi.fn(),
        onStream: vi.fn(),
        onPreview,
        onNotFound,
        onTrackUpdated: vi.fn(),
        isStale: () => false,
      },
    );
    expect(onNotFound).toHaveBeenCalled();
    expect(onPreview).not.toHaveBeenCalled();
  });

  it('5. recovery skips failed provider', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'audius',
        playable_url: 'https://api.audius.co/v1/tracks/1/stream',
        status: 'ok',
      }),
    );
    resolver.recoverFromPlaybackError(track(), 'youtube', {
      onResolving: vi.fn(),
      onYoutube: vi.fn(),
      onStream: vi.fn(),
      onPreview: vi.fn(),
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(getAudioSource).toHaveBeenCalledWith(1, {
      force: true,
      skipProvider: 'youtube',
      asyncResolve: false,
    });
  });

  it('6. API error becomes unavailable (not generic demo)', () => {
    getAudioSource.mockReturnValue(throwError(() => ({ status: 500 })));
    const onPreview = vi.fn();
    const onNotFound = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube: vi.fn(),
      onStream: vi.fn(),
      onPreview,
      onNotFound,
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onNotFound).toHaveBeenCalled();
    expect(onPreview).not.toHaveBeenCalled();
  });

  it('7. track-specific preview URL is allowed', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'preview',
        playable_url: 'https://cdn.example/track-1-preview.mp3',
        status: 'ok',
      }),
    );
    const onPreview = vi.fn();
    const onNotFound = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube: vi.fn(),
      onStream: vi.fn(),
      onPreview,
      onNotFound,
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onPreview).toHaveBeenCalledWith('https://cdn.example/track-1-preview.mp3');
    expect(onNotFound).not.toHaveBeenCalled();
  });

  it('8. stale callback ignores late resolve', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'youtube',
        youtube_video_id: 'late-id',
        status: 'ok',
      }),
    );
    const onYoutube = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube,
      onStream: vi.fn(),
      onPreview: vi.fn(),
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => true,
    });
    expect(onYoutube).not.toHaveBeenCalled();
  });
});
