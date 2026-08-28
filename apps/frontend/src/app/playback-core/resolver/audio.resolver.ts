import { Injectable, inject, isDevMode } from '@angular/core';
import { Observable, Subscription, TimeoutError, race, timer } from 'rxjs';
import { map, take } from 'rxjs/operators';
import { PlayableTrack } from '../../shared/models/player.models';
import { AudioSource } from '../../shared/models/api.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { isGenericToneAudioUrl } from '../../shared/config/generic-tone-audio.config';
import {
  ResolvedPlaybackSource,
  RESOLVE_FRIENDLY_ERROR,
  isPlayableSource,
  mapAudioSourceResponse,
} from './resolved-source.model';
import { SpotifyIntegrationService } from '../../core/integrations/spotify/spotify-integration.service';

export type PlaybackEngineMode = 'spotify' | 'stream' | 'preview' | 'loading';

/** Clear resolve lifecycle for the player UI. */
export type AudioResolvePhase =
  | 'idle'
  | 'resolving'
  | 'ready'
  | 'playing'
  | 'failed'
  | 'unavailable';

export interface AudioResolveDiagnostics {
  trackId: number;
  requestId: number;
  cacheHit: boolean | null;
  providersTried: string[];
  elapsedMs: number;
  fallbackReason: string | null;
}

export interface AudioResolveCallbacks {
  onResolving: () => void;
  onSpotify?: (uri: string) => void;
  onStream: (streamUrl: string) => void;
  /** Track-specific Deezer preview URL only. */
  onPreview: (previewUrl: string) => void;
  /** Terminal no-source result. The reason is diagnostic only. */
  onNotFound: (reason?: string) => void;
  onTrackUpdated: (track: PlayableTrack) => void;
  isStale: () => boolean;
  onDiagnostics?: (diag: AudioResolveDiagnostics) => void;
}

const PROVIDER_TIMEOUT_MS = 18_000;
const PENDING_POLL_MAX = 10;

/** Spotify catalog playback with a Deezer 30-second preview fallback. */
@Injectable({ providedIn: 'root' })
export class AudioResolver {
  private readonly tracksApi = inject(TracksService);
  private readonly history = inject(HistoryService);
  private readonly spotify = inject(SpotifyIntegrationService);
  private readonly inFlight = new Map<number, Subscription>();
  private requestSeq = 0;

  readonly friendlyError = RESOLVE_FRIENDLY_ERROR;
  /** Last resolve diagnostics (dev only; never shown in UI). */
  lastDiagnostics: AudioResolveDiagnostics | null = null;

  resetRetries(): void {
    // Kept as a compatibility seam for callers that reset playback recovery.
  }

  forgetRetry(_trackId: number): void {
    // Spotify → Deezer has no candidate-exclusion retry state.
  }

  cancel(trackId?: number): void {
    if (trackId != null) {
      this.inFlight.get(trackId)?.unsubscribe();
      this.inFlight.delete(trackId);
      return;
    }
    for (const sub of this.inFlight.values()) sub.unsubscribe();
    this.inFlight.clear();
  }

  resolvePlayableSource(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    options: { spotifyOnly?: boolean } = {},
  ): void {
    if (options.spotifyOnly && (!callbacks.onSpotify || !this.spotify.connected())) {
      this.emitDiag(track.id, 0, false, ['spotify'], 0, 'spotify_disconnected', callbacks);
      callbacks.onNotFound('spotify_disconnected');
      return;
    }

    if (callbacks.onSpotify && this.spotify.connected()) {
      const knownUri = track.spotifyUri ?? (
        track.spotifyTrackId ? `spotify:track:${track.spotifyTrackId}` : undefined
      );
      if (knownUri) {
        this.emitDiag(track.id, 0, true, ['spotify'], 0, null, callbacks);
        callbacks.onSpotify(knownUri);
        return;
      }

      this.cancel(track.id);
      const requestId = ++this.requestSeq;
      const started = performance.now();
      callbacks.onResolving();
      const sub = this.tracksApi.getTrackById(track.id).subscribe({
        next: (detail) => {
          if (callbacks.isStale()) return;
          if (detail.spotify_track_id) {
            const updated = {
              ...track,
              spotifyTrackId: detail.spotify_track_id,
              spotifyUri: `spotify:track:${detail.spotify_track_id}`,
            };
            callbacks.onTrackUpdated(updated);
            this.emitDiag(track.id, requestId, false, ['spotify'], performance.now() - started, null, callbacks);
            callbacks.onSpotify?.(updated.spotifyUri);
            return;
          }
          if (options.spotifyOnly) {
            this.emitDiag(track.id, requestId, false, ['spotify'], performance.now() - started, 'spotify_id_missing', callbacks);
            callbacks.onNotFound('spotify_id_missing');
            return;
          }
          this.resolveDeezer(track, callbacks, requestId, started, ['spotify']);
        },
        error: () => {
          if (callbacks.isStale()) return;
          if (options.spotifyOnly) {
            callbacks.onNotFound('spotify_lookup_failed');
            return;
          }
          this.resolveDeezer(track, callbacks, requestId, started, ['spotify']);
        },
      });
      this.inFlight.set(track.id, sub);
      return;
    }

    if (options.spotifyOnly) {
      callbacks.onNotFound('spotify_disconnected');
      return;
    }
    this.resolveDeezer(track, callbacks);
  }

  recoverFromPlaybackError(
    track: PlayableTrack,
    failedProvider: 'spotify' | 'preview' | 'stream',
    callbacks: AudioResolveCallbacks,
  ): void {
    // Spotify may fail after the catalog lookup (Premium/device/session issue),
    // so make one explicit Deezer resolution. A failed Deezer/local preview is
    // terminal for this track and is handled by the queue auto-skip layer.
    if (failedProvider !== 'spotify') {
      callbacks.onNotFound(`${failedProvider}_unavailable`);
      return;
    }
    this.resolveDeezer(track, callbacks, ++this.requestSeq, performance.now(), ['spotify'], true);
  }

  private resolveDeezer(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    requestId = ++this.requestSeq,
    started = performance.now(),
    providersTried: string[] = [],
    fromRecovery = false,
  ): void {
    this.cancel(track.id);
    callbacks.onResolving();
    const sub = this.fetchSource(track.id, { force: fromRecovery, asyncResolve: false }).subscribe({
      next: (src) => {
        if (callbacks.isStale()) return;
        this.handleResponse(track, src, callbacks, requestId, started, providersTried, !fromRecovery);
      },
      error: (err) => {
        if (callbacks.isStale()) return;
        this.handleFetchError(track, err, callbacks, requestId, started, providersTried);
      },
    });
    this.inFlight.set(track.id, sub);
  }

  private fetchSource(
    trackId: number,
    opts: { force?: boolean; asyncResolve?: boolean },
  ): Observable<AudioSource> {
    return race(
      this.tracksApi.getAudioSource(trackId, opts),
      timer(PROVIDER_TIMEOUT_MS).pipe(map(() => { throw new TimeoutError(); })),
    ).pipe(take(1));
  }

  private handleFetchError(
    track: PlayableTrack,
    err: unknown,
    callbacks: AudioResolveCallbacks,
    requestId: number,
    started: number,
    providersTried: string[],
  ): void {
    const status = (err as { status?: number })?.status;
    if (status === 429) {
      window.setTimeout(() => {
        if (callbacks.isStale()) return;
        const sub = this.fetchSource(track.id, { force: true, asyncResolve: false }).subscribe({
          next: (src) => this.handleResponse(track, src, callbacks, requestId, started, providersTried, false),
          error: () => this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'http_429_retry_failed'),
        });
        this.inFlight.set(track.id, sub);
      }, 800);
      return;
    }
    if (status === 404) this.history.remove(track.id);
    const reason = err instanceof TimeoutError ? 'provider_timeout' : `http_${status ?? 'error'}`;
    this.finishUnavailable(track, callbacks, requestId, started, providersTried, reason);
  }

  private handleResponse(
    track: PlayableTrack,
    src: AudioSource,
    callbacks: AudioResolveCallbacks,
    requestId: number,
    started: number,
    providersTried: string[],
    cacheHit: boolean,
  ): void {
    if (callbacks.isStale()) return;
    if (src.status === 'pending') {
      this.pollPendingSource(track, callbacks, 0, requestId, started, providersTried);
      return;
    }
    this.applyResolved(track, mapAudioSourceResponse(src), callbacks, requestId, started, providersTried, cacheHit);
  }

  private pollPendingSource(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    attempt: number,
    requestId: number,
    started: number,
    providersTried: string[],
  ): void {
    const delayMs = attempt === 0 ? 600 : Math.min(2500, 600 + attempt * 350);
    const timerId = window.setTimeout(() => {
      if (callbacks.isStale()) return;
      const sub = this.fetchSource(track.id, { asyncResolve: true }).subscribe({
        next: (retry) => {
          if (callbacks.isStale()) return;
          if (retry.status === 'pending' && attempt + 1 < PENDING_POLL_MAX) {
            this.pollPendingSource(track, callbacks, attempt + 1, requestId, started, providersTried);
            return;
          }
          if (retry.status === 'pending') {
            this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'pending_timeout');
            return;
          }
          this.applyResolved(track, mapAudioSourceResponse(retry), callbacks, requestId, started, providersTried, false);
        },
        error: () => this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'pending_poll_error'),
      });
      this.inFlight.set(track.id, sub);
    }, delayMs);
    this.inFlight.set(track.id, new Subscription(() => clearTimeout(timerId)));
  }

  private applyResolved(
    track: PlayableTrack,
    resolved: ResolvedPlaybackSource,
    callbacks: AudioResolveCallbacks,
    requestId: number,
    started: number,
    providersTried: string[],
    cacheHit: boolean,
  ): void {
    if (callbacks.isStale()) return;
    if (resolved.provider && resolved.provider !== 'none') providersTried.push(resolved.provider);

    if (
      (resolved.provider === 'demo' || resolved.provider === 'preview' || resolved.provider === 'deezer') &&
      resolved.streamUrl &&
      !isGenericToneAudioUrl(resolved.streamUrl)
    ) {
      this.emitDiag(track.id, requestId, cacheHit, providersTried, started, 'deezer_preview', callbacks);
      callbacks.onTrackUpdated({ ...track, audioUrl: resolved.streamUrl });
      callbacks.onPreview(resolved.streamUrl);
      return;
    }

    if (resolved.provider === 'local_published' && resolved.streamUrl) {
      this.emitDiag(track.id, requestId, cacheHit, providersTried, started, null, callbacks);
      callbacks.onTrackUpdated({ ...track, audioUrl: resolved.streamUrl });
      callbacks.onStream(resolved.streamUrl);
      return;
    }

    if (!isPlayableSource(resolved)) {
      this.finishUnavailable(track, callbacks, requestId, started, providersTried, resolved.status || 'not_playable');
      return;
    }
    this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'unmapped_provider');
  }

  private finishUnavailable(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    requestId: number,
    started: number,
    providersTried: string[],
    reason: string,
  ): void {
    if (track.audioUrl && isGenericToneAudioUrl(track.audioUrl)) {
      reason = `blocked_generic_demo:${reason}`;
    }
    this.emitDiag(track.id, requestId, false, providersTried, started, reason, callbacks);
    callbacks.onNotFound(reason);
  }

  private emitDiag(
    trackId: number,
    requestId: number,
    cacheHit: boolean | null,
    providersTried: string[],
    startedOrElapsed: number,
    fallbackReason: string | null,
    callbacks: AudioResolveCallbacks,
  ): void {
    const elapsedMs =
      startedOrElapsed > 1_000_000
        ? Math.round(performance.now() - startedOrElapsed)
        : Math.round(startedOrElapsed);
    const diag: AudioResolveDiagnostics = {
      trackId,
      requestId,
      cacheHit,
      providersTried: [...providersTried],
      elapsedMs,
      fallbackReason,
    };
    this.lastDiagnostics = diag;
    callbacks.onDiagnostics?.(diag);
    if (isDevMode()) console.debug('[AudioResolver]', diag);
  }
}
