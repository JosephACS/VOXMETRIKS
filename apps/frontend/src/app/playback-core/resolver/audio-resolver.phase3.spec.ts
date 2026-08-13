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
        {
          provide: TracksService,
          useValue: {
            getAudioSource,
            reportAudioSourceFailure: vi.fn().mockReturnValue(of({ track_id: 1, status: 'recorded' })),
          },
        },
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

  it('4. not_found force-retries once then onNotFound if still empty', () => {
    getAudioSource
      .mockReturnValueOnce(of({ track_id: 1, provider: 'audius', status: 'not_found' }))
      .mockReturnValueOnce(of({ track_id: 1, provider: 'audius', status: 'not_found' }));
    const onNotFound = vi.fn();
    const onPreview = vi.fn();
    const onResolving = vi.fn();
    resolver.resolvePlayableSource(
      { ...track(), audioUrl: '/assets/audio/demo-01.wav' },
      {
        onResolving,
        onYoutube: vi.fn(),
        onStream: vi.fn(),
        onPreview,
        onNotFound,
        onTrackUpdated: vi.fn(),
        isStale: () => false,
      },
    );
    expect(getAudioSource).toHaveBeenCalledTimes(2);
    expect(getAudioSource).toHaveBeenLastCalledWith(1, { force: true, asyncResolve: false });
    expect(onNotFound).toHaveBeenCalled();
    expect(onPreview).not.toHaveBeenCalled();
  });

  it('4b. not_found then force YouTube ok recovers without surfacing failure', () => {
    getAudioSource
      .mockReturnValueOnce(of({ track_id: 1, provider: 'audius', status: 'not_found' }))
      .mockReturnValueOnce(
        of({
          track_id: 1,
          provider: 'youtube',
          youtube_video_id: 'recovered',
          status: 'ok',
        }),
      );
    const onYoutube = vi.fn();
    const onNotFound = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube,
      onStream: vi.fn(),
      onPreview: vi.fn(),
      onNotFound,
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onYoutube).toHaveBeenCalledWith('recovered');
    expect(onNotFound).not.toHaveBeenCalled();
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

  it('5b. youtube playback failure excludes video and tries next candidate', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'youtube',
        youtube_video_id: 'alt-id',
        status: 'ok',
      }),
    );
    const onYoutube = vi.fn();
    resolver.recoverFromPlaybackError(
      { ...track(), youtubeVideoId: 'bad-id' },
      'youtube',
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
    expect(getAudioSource).toHaveBeenCalledWith(1, {
      force: true,
      excludeSourceRef: 'bad-id',
      asyncResolve: false,
    });
    expect(onYoutube).toHaveBeenCalledWith('alt-id');
  });

  it('5c. after exclude without fresh youtube, skips youtube provider (no loop)', () => {
    getAudioSource
      .mockReturnValueOnce(
        of({
          track_id: 1,
          provider: 'audius',
          status: 'not_found',
        }),
      )
      .mockReturnValueOnce(
        of({
          track_id: 1,
          provider: 'audius',
          playable_url: 'https://api.audius.co/v1/tracks/1/stream',
          status: 'ok',
        }),
      );
    const onStream = vi.fn();
    const onNotFound = vi.fn();
    resolver.recoverFromPlaybackError(
      { ...track(), youtubeVideoId: 'bad-id' },
      'youtube',
      {
        onResolving: vi.fn(),
        onYoutube: vi.fn(),
        onStream,
        onPreview: vi.fn(),
        onNotFound,
        onTrackUpdated: vi.fn(),
        isStale: () => false,
      },
    );
    expect(getAudioSource).toHaveBeenNthCalledWith(1, 1, {
      force: true,
      excludeSourceRef: 'bad-id',
      asyncResolve: false,
    });
    expect(getAudioSource).toHaveBeenNthCalledWith(2, 1, {
      force: true,
      skipProvider: 'youtube',
      asyncResolve: false,
    });
    expect(onStream).toHaveBeenCalled();
    expect(onNotFound).not.toHaveBeenCalled();
  });

  it('5d. recursive youtube recovery without videoId still excludes prior ids', () => {
    // Simulate: first candidate already recorded, track.youtubeVideoId cleared.
    (resolver as unknown as { failedProviders: Map<number, Set<string>> }).failedProviders.set(
      1,
      new Set(['yt:first-id']),
    );
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'youtube',
        youtube_video_id: 'third-id',
        status: 'ok',
      }),
    );
    const onYoutube = vi.fn();
    resolver.recoverFromPlaybackError(
      { ...track(), youtubeVideoId: undefined },
      'youtube',
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
    expect(getAudioSource).toHaveBeenCalledWith(1, {
      force: true,
      excludeSourceRef: 'first-id',
      asyncResolve: false,
    });
    expect(onYoutube).toHaveBeenCalledWith('third-id');
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
