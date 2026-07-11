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
    audioUrl: '/assets/audio/demo-01.wav',
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
        onDemo: vi.fn(),
        onNotFound: vi.fn(),
        onTrackUpdated: vi.fn(),
        isStale: () => false,
      },
    );
    expect(onYoutube).toHaveBeenCalledWith('cached-id');
    expect(getAudioSource).not.toHaveBeenCalled();
  });

  it('2. resolves uncached track via API', () => {
    getAudioSource.mockReturnValue(
      of({
        track_id: 1,
        provider: 'youtube',
        youtube_video_id: 'new-id',
        status: 'ok',
      }),
    );
    const onYoutube = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube,
      onStream: vi.fn(),
      onDemo: vi.fn(),
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(getAudioSource).toHaveBeenCalled();
    expect(onYoutube).toHaveBeenCalledWith('new-id');
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
      onDemo: vi.fn(),
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onStream).toHaveBeenCalledWith('https://api.audius.co/v1/tracks/55/stream');
  });

  it('4. not_found triggers onNotFound callback', () => {
    getAudioSource.mockReturnValue(
      of({ track_id: 1, provider: 'youtube', status: 'not_found' }),
    );
    const onNotFound = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube: vi.fn(),
      onStream: vi.fn(),
      onDemo: vi.fn(),
      onNotFound,
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onNotFound).toHaveBeenCalled();
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
      onDemo: vi.fn(),
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(getAudioSource).toHaveBeenCalledWith(1, true, 'youtube');
  });

  it('6. API error falls back to demo', () => {
    getAudioSource.mockReturnValue(throwError(() => ({ status: 500 })));
    const onDemo = vi.fn();
    resolver.resolvePlayableSource(track(), {
      onResolving: vi.fn(),
      onYoutube: vi.fn(),
      onStream: vi.fn(),
      onDemo,
      onNotFound: vi.fn(),
      onTrackUpdated: vi.fn(),
      isStale: () => false,
    });
    expect(onDemo).toHaveBeenCalled();
  });
});
