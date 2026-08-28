import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AudioResolver, AudioResolveCallbacks } from './audio.resolver';
import { PlayableTrack } from '../../shared/models/player.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { SpotifyIntegrationService } from '../../core/integrations/spotify/spotify-integration.service';

const track = (overrides: Partial<PlayableTrack> = {}): PlayableTrack => ({
  id: 7,
  title: 'Test track',
  artist: 'Test artist',
  audioUrl: '',
  coverGradient: 'linear-gradient(135deg,#111,#333)',
  ...overrides,
});

function callbacks(): AudioResolveCallbacks & {
  onSpotify: ReturnType<typeof vi.fn>;
  onStream: ReturnType<typeof vi.fn>;
  onPreview: ReturnType<typeof vi.fn>;
  onNotFound: ReturnType<typeof vi.fn>;
  onTrackUpdated: ReturnType<typeof vi.fn>;
} {
  return {
    onResolving: vi.fn(),
    onSpotify: vi.fn(),
    onStream: vi.fn(),
    onPreview: vi.fn(),
    onNotFound: vi.fn(),
    onTrackUpdated: vi.fn(),
    isStale: () => false,
  } as unknown as AudioResolveCallbacks & {
    onSpotify: ReturnType<typeof vi.fn>;
    onStream: ReturnType<typeof vi.fn>;
    onPreview: ReturnType<typeof vi.fn>;
    onNotFound: ReturnType<typeof vi.fn>;
    onTrackUpdated: ReturnType<typeof vi.fn>;
  };
}

describe('AudioResolver · Spotify → Deezer', () => {
  let resolver: AudioResolver;
  let tracks: { getTrackById: ReturnType<typeof vi.fn>; getAudioSource: ReturnType<typeof vi.fn> };
  let spotify: { connected: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    tracks = {
      getTrackById: vi.fn(() => of({ spotify_track_id: null })),
      getAudioSource: vi.fn(() => of({ track_id: 7, provider: 'deezer', status: 'ok', playable_url: 'https://cdn.test/preview.mp3' })),
    };
    spotify = { connected: vi.fn(() => false) };
    TestBed.configureTestingModule({
      providers: [
        AudioResolver,
        { provide: TracksService, useValue: tracks },
        { provide: HistoryService, useValue: { remove: vi.fn() } },
        { provide: SpotifyIntegrationService, useValue: spotify },
      ],
    });
    resolver = TestBed.inject(AudioResolver);
  });

  it('uses a known Spotify URI without calling the backend', () => {
    spotify.connected.mockReturnValue(true);
    const cb = callbacks();
    resolver.resolvePlayableSource(track({ spotifyTrackId: 'sp-7' }), cb);
    expect(cb.onSpotify).toHaveBeenCalledWith('spotify:track:sp-7');
    expect(tracks.getAudioSource).not.toHaveBeenCalled();
  });

  it('looks up Spotify identity before falling back to Deezer', () => {
    spotify.connected.mockReturnValue(true);
    tracks.getTrackById.mockReturnValue(of({ spotify_track_id: 'sp-7' }));
    const cb = callbacks();
    resolver.resolvePlayableSource(track(), cb);
    expect(cb.onSpotify).toHaveBeenCalledWith('spotify:track:sp-7');
    expect(cb.onPreview).not.toHaveBeenCalled();
  });

  it('resolves a Deezer preview when Spotify is disconnected', () => {
    const cb = callbacks();
    resolver.resolvePlayableSource(track(), cb);
    expect(cb.onPreview).toHaveBeenCalledWith('https://cdn.test/preview.mp3');
  });

  it('falls back to Deezer when Spotify lookup fails', () => {
    spotify.connected.mockReturnValue(true);
    tracks.getTrackById.mockReturnValue(throwError(() => new Error('lookup failed')));
    const cb = callbacks();
    resolver.resolvePlayableSource(track(), cb);
    expect(cb.onPreview).toHaveBeenCalledWith('https://cdn.test/preview.mp3');
  });

  it('reports a terminal no-source response to the player', () => {
    tracks.getAudioSource.mockReturnValue(of({ track_id: 7, provider: 'deezer', status: 'not_found', playable_url: null }));
    const cb = callbacks();
    resolver.resolvePlayableSource(track(), cb);
    expect(cb.onNotFound).toHaveBeenCalled();
  });

  it('recovers a Spotify transport error through Deezer', () => {
    spotify.connected.mockReturnValue(true);
    const cb = callbacks();
    resolver.recoverFromPlaybackError(track({ spotifyTrackId: 'sp-7' }), 'spotify', cb);
    expect(cb.onPreview).toHaveBeenCalledWith('https://cdn.test/preview.mp3');
  });
});
