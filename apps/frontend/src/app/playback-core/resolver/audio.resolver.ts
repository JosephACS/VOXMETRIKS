import { Injectable, inject, isDevMode } from '@angular/core';
import {
  Observable,
  Subscription,
  TimeoutError,
  of,
  race,
  timer,
} from 'rxjs';
import { catchError, map, switchMap, take } from 'rxjs/operators';
import { PlayableTrack } from '../../shared/models/player.models';
import { AudioSource } from '../../shared/models/api.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { isGenericDemoAudioUrl } from '../../shared/config/demo-audio.config';
import {
  ResolvedPlaybackSource,
  RESOLVE_FRIENDLY_ERROR,
  isPlayableSource,
  mapAudioSourceResponse,
} from './resolved-source.model';

export type PlaybackEngineMode = 'youtube' | 'stream' | 'preview' | 'loading';

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
  onYoutube: (videoId: string) => void;
  onStream: (streamUrl: string) => void;
  /** Track-specific preview URL only (never a generic catalog demo tone). */
  onPreview: (previewUrl: string) => void;
  onNotFound: () => void;
  onTrackUpdated: (track: PlayableTrack) => void;
  isStale: () => boolean;
  onDiagnostics?: (diag: AudioResolveDiagnostics) => void;
}

const PROVIDER_TIMEOUT_MS = 18_000;
const PENDING_POLL_MAX = 10;

/**
 * Central audio resolver — cache → YouTube → Audius → track preview → unavailable.
 * Never treats generic `/assets/audio/demo-*.wav` as the selected song.
 */
@Injectable({ providedIn: 'root' })
export class AudioResolver {
  private readonly tracksApi = inject(TracksService);
  private readonly history = inject(HistoryService);
  private readonly failedProviders = new Map<number, Set<string>>();
  private readonly inFlight = new Map<number, Subscription>();
  private requestSeq = 0;

  readonly friendlyError = RESOLVE_FRIENDLY_ERROR;
  /** Last resolve diagnostics (dev only; never shown in UI). */
  lastDiagnostics: AudioResolveDiagnostics | null = null;

  resetRetries(): void {
    this.failedProviders.clear();
  }

  forgetRetry(trackId: number): void {
    this.failedProviders.delete(trackId);
  }

  /** Cancel any in-flight HTTP/poll for a track (user selected another song). */
  cancel(trackId?: number): void {
    if (trackId != null) {
      this.inFlight.get(trackId)?.unsubscribe();
      this.inFlight.delete(trackId);
      return;
    }
    for (const sub of this.inFlight.values()) sub.unsubscribe();
    this.inFlight.clear();
  }

  resolvePlayableSource(track: PlayableTrack, callbacks: AudioResolveCallbacks): void {
    if (track.youtubeVideoId) {
      this.emitDiag(track.id, 0, true, ['youtube-cached'], 0, null, callbacks);
      callbacks.onYoutube(track.youtubeVideoId);
      return;
    }

    this.cancel(track.id);
    const requestId = ++this.requestSeq;
    const started = performance.now();
    const providersTried: string[] = [];
    callbacks.onResolving();

    // User play: wait for sync resolution (async_resolve=false) so first click can autoplay.
    const sub = this.fetchSource(track.id, { asyncResolve: false }).subscribe({
      next: (src) => {
        if (callbacks.isStale()) return;
        this.handleResponse(track, src, callbacks, false, requestId, started, providersTried);
      },
      error: (err) => {
        if (callbacks.isStale()) return;
        this.handleFetchError(track, err, callbacks, requestId, started, providersTried);
      },
    });
    this.inFlight.set(track.id, sub);
  }

  recoverFromPlaybackError(
    track: PlayableTrack,
    failedProvider: 'youtube' | 'stream' | 'preview',
    callbacks: AudioResolveCallbacks,
  ): void {
    if (failedProvider === 'preview') {
      callbacks.onNotFound();
      return;
    }

    const tried = this.failedProviders.get(track.id) ?? new Set<string>();

    // YouTube: keep requesting next video candidates (accumulate excludes) before
    // abandoning the provider. Do not require track.youtubeVideoId on every call —
    // it is cleared after each failed candidate to avoid cache reuse, but prior
    // yt: ids remain in `tried` so recovery can still ask for the next candidate.
    if (failedProvider === 'youtube') {
      if (track.youtubeVideoId) {
        tried.add(`yt:${track.youtubeVideoId}`);
      }
      this.failedProviders.set(track.id, tried);
      const excludedIds = [...tried]
        .filter((k) => k.startsWith('yt:') && k !== 'yt:__done__')
        .map((k) => k.slice(3));

      if (
        !tried.has('youtube') &&
        !tried.has('yt:__done__') &&
        excludedIds.length > 0 &&
        excludedIds.length <= 4
      ) {
        this.cancel(track.id);
        const requestId = ++this.requestSeq;
        const started = performance.now();
        const providersTried = ['youtube', ...excludedIds.map((id) => `exclude:${id}`)];
        const cleared = { ...track, youtubeVideoId: undefined };
        callbacks.onTrackUpdated(cleared);
        callbacks.onResolving();
        // Wait for failure report so the backend can warm ranked YouTube alternates
        // before the exclude resolve (avoids a second flaky Data API search).
        const sub = this.tracksApi.reportAudioSourceFailure(track.id).pipe(
          // Always continue to exclude resolve, even if reporting fails.
          catchError(() => of(null)),
          switchMap(() =>
            this.fetchSource(track.id, {
              force: true,
              excludeSourceRef: excludedIds.join(','),
              asyncResolve: false,
            }),
          ),
        ).subscribe({
          next: (src) => {
            if (callbacks.isStale()) return;
            const mapped = mapAudioSourceResponse(src);
            if (
              mapped.provider === 'youtube' &&
              mapped.youtubeVideoId &&
              !tried.has(`yt:${mapped.youtubeVideoId}`) &&
              isPlayableSource(mapped)
            ) {
              this.handleResponse(cleared, src, callbacks, true, requestId, started, providersTried);
              return;
            }
            // No fresh YouTube candidate — stop exclude loop; skip YouTube next.
            tried.add('yt:__done__');
            this.failedProviders.set(track.id, tried);
            this.recoverFromPlaybackError(cleared, 'youtube', callbacks);
          },
          error: () => {
            if (!callbacks.isStale()) {
              tried.add('yt:__done__');
              this.failedProviders.set(track.id, tried);
              this.recoverFromPlaybackError(cleared, 'youtube', callbacks);
            }
          },
        });
        this.inFlight.set(track.id, sub);
        return;
      }
    }

    this.tracksApi.reportAudioSourceFailure(track.id).subscribe({ error: () => undefined });

    const skip = failedProvider === 'stream' ? 'audius' : failedProvider;
    if (tried.has(skip)) {
      this.finishUnavailable(track, callbacks, ++this.requestSeq, performance.now(), [skip], 'providers_exhausted');
      return;
    }
    tried.add(skip);
    this.failedProviders.set(track.id, tried);

    this.cancel(track.id);
    const requestId = ++this.requestSeq;
    const started = performance.now();
    const providersTried = [skip];
    const cleared =
      failedProvider === 'youtube' ? { ...track, youtubeVideoId: undefined } : track;
    if (cleared !== track) callbacks.onTrackUpdated(cleared);
    callbacks.onResolving();

    const sub = this.fetchSource(track.id, {
      force: true,
      skipProvider: skip,
      asyncResolve: false,
    }).subscribe({
      next: (src) => {
        if (callbacks.isStale()) return;
        this.handleResponse(cleared, src, callbacks, true, requestId, started, providersTried);
      },
      error: () => {
        if (!callbacks.isStale()) {
          this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'recovery_http_error');
        }
      },
    });
    this.inFlight.set(track.id, sub);
  }

  private fetchSource(
    trackId: number,
    opts: {
      force?: boolean;
      skipProvider?: string;
      excludeSourceRef?: string;
      asyncResolve?: boolean;
    },
  ): Observable<AudioSource> {
    return race(
      this.tracksApi.getAudioSource(trackId, opts),
      timer(PROVIDER_TIMEOUT_MS).pipe(
        map(() => {
          throw new TimeoutError();
        }),
      ),
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
        const sub = this.fetchSource(track.id, { asyncResolve: false }).subscribe({
          next: (src) => this.handleResponse(track, src, callbacks, false, requestId, started, providersTried),
          error: (retryErr) => {
            if (callbacks.isStale()) return;
            if ((retryErr as { status?: number })?.status === 404) this.history.remove(track.id);
            this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'http_429_retry_failed');
          },
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
    fromRecovery: boolean,
    requestId: number,
    started: number,
    providersTried: string[],
  ): void {
    if (callbacks.isStale()) return;

    if (src.status === 'pending') {
      this.pollPendingSource(track, callbacks, 0, fromRecovery, requestId, started, providersTried);
      return;
    }

    const cacheHit = src.status === 'ok' && !fromRecovery;
    this.applyResolved(
      track,
      mapAudioSourceResponse(src),
      callbacks,
      requestId,
      started,
      providersTried,
      cacheHit,
      fromRecovery,
    );
  }

  private pollPendingSource(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    attempt: number,
    fromRecovery: boolean,
    requestId: number,
    started: number,
    providersTried: string[],
  ): void {
    const delayMs = attempt === 0 ? 600 : Math.min(2500, 600 + attempt * 350);
    const timerId = window.setTimeout(() => {
      if (callbacks.isStale()) return;
      const skip = fromRecovery ? this.lastSkipProvider(track.id) : undefined;
      const sub = this.fetchSource(track.id, {
        asyncResolve: true,
        skipProvider: skip,
      }).subscribe({
        next: (retry) => {
          if (callbacks.isStale()) return;
          if (retry.status === 'pending' && attempt + 1 < PENDING_POLL_MAX) {
            this.pollPendingSource(
              track, callbacks, attempt + 1, fromRecovery, requestId, started, providersTried,
            );
            return;
          }
          if (retry.status === 'pending') {
            this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'pending_timeout');
            return;
          }
          this.applyResolved(
            track,
            mapAudioSourceResponse(retry),
            callbacks,
            requestId,
            started,
            providersTried,
            false,
            fromRecovery,
          );
        },
        error: () => {
          if (!callbacks.isStale()) {
            this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'pending_poll_error');
          }
        },
      });
      this.inFlight.set(track.id, sub);
    }, delayMs);

    // Allow cancel() to clear pending polls via a dummy subscription.
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
    fromRecovery = false,
  ): void {
    if (callbacks.isStale()) return;
    if (resolved.provider && resolved.provider !== 'none') {
      providersTried.push(resolved.provider);
    }

    // Track-specific preview (explicit provider) — never generic demo WAV.
    if (
      (resolved.provider === 'demo' || resolved.provider === 'preview') &&
      resolved.streamUrl &&
      !isGenericDemoAudioUrl(resolved.streamUrl)
    ) {
      this.emitDiag(track.id, requestId, cacheHit, providersTried, started, 'track_preview', callbacks);
      callbacks.onPreview(resolved.streamUrl);
      return;
    }

    if (!isPlayableSource(resolved)) {
      // Negative/partial cache can hide a working alternate provider.
      // One silent force re-resolve while UI stays on "Preparando…".
      if (!fromRecovery) {
        this.retryForceResolve(track, callbacks, requestId, started, providersTried);
        return;
      }
      this.finishUnavailable(track, callbacks, requestId, started, providersTried, resolved.status || 'not_playable');
      return;
    }

    if (resolved.provider === 'youtube' && resolved.youtubeVideoId) {
      callbacks.onTrackUpdated({ ...track, youtubeVideoId: resolved.youtubeVideoId });
      this.emitDiag(track.id, requestId, cacheHit, providersTried, started, null, callbacks);
      callbacks.onYoutube(resolved.youtubeVideoId);
      return;
    }

    if (
      (resolved.provider === 'audius' || resolved.provider === 'local_published') &&
      resolved.streamUrl
    ) {
      callbacks.onTrackUpdated({ ...track, audioUrl: resolved.streamUrl });
      this.emitDiag(track.id, requestId, cacheHit, providersTried, started, null, callbacks);
      callbacks.onStream(resolved.streamUrl);
      return;
    }

    this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'unmapped_provider');
  }

  private retryForceResolve(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    requestId: number,
    started: number,
    providersTried: string[],
  ): void {
    callbacks.onResolving();
    const sub = this.fetchSource(track.id, { force: true, asyncResolve: false }).subscribe({
      next: (src) => {
        if (callbacks.isStale()) return;
        if (src.status === 'pending') {
          this.pollPendingSource(track, callbacks, 0, true, requestId, started, providersTried);
          return;
        }
        const forced = mapAudioSourceResponse(src);
        if (!isPlayableSource(forced)) {
          this.finishUnavailable(
            track,
            callbacks,
            requestId,
            started,
            providersTried,
            forced.status || 'not_playable_after_force',
          );
          return;
        }
        this.applyResolved(track, forced, callbacks, requestId, started, providersTried, false, true);
      },
      error: () => {
        if (!callbacks.isStale()) {
          this.finishUnavailable(track, callbacks, requestId, started, providersTried, 'force_retry_http_error');
        }
      },
    });
    this.inFlight.set(track.id, sub);
  }

  private finishUnavailable(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    requestId: number,
    started: number,
    providersTried: string[],
    reason: string,
  ): void {
    // Explicitly refuse generic demo tones attached by adapters.
    if (track.audioUrl && isGenericDemoAudioUrl(track.audioUrl)) {
      this.emitDiag(track.id, requestId, false, providersTried, started, `blocked_generic_demo:${reason}`, callbacks);
      callbacks.onNotFound();
      return;
    }
    this.emitDiag(track.id, requestId, false, providersTried, started, reason, callbacks);
    callbacks.onNotFound();
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
    if (isDevMode()) {
      // Dev-only; no tokens/cookies/full URLs.
      console.debug('[AudioResolver]', {
        trackId: diag.trackId,
        requestId: diag.requestId,
        cacheHit: diag.cacheHit,
        providersTried: diag.providersTried,
        elapsedMs: diag.elapsedMs,
        fallbackReason: diag.fallbackReason,
      });
    }
  }

  private lastSkipProvider(trackId: number): string | undefined {
    const set = this.failedProviders.get(trackId);
    if (!set?.size) return undefined;
    return [...set].at(-1);
  }
}
