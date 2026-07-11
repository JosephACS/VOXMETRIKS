import { Injectable, inject } from '@angular/core';
import { PlayableTrack } from '../../shared/models/player.models';
import { AudioSource } from '../../shared/models/api.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import {
  ResolvedPlaybackSource,
  RESOLVE_FRIENDLY_ERROR,
  isPlayableSource,
  mapAudioSourceResponse,
} from './resolved-source.model';

export type PlaybackEngineMode = 'youtube' | 'stream' | 'demo' | 'loading';

export interface AudioResolveCallbacks {
  onResolving: () => void;
  onYoutube: (videoId: string) => void;
  onStream: (streamUrl: string) => void;
  onDemo: () => void;
  onNotFound: () => void;
  onTrackUpdated: (track: PlayableTrack) => void;
  isStale: () => boolean;
}

/**
 * Central audio resolver — single entry for playback source resolution.
 * Components must not branch on provider; only this class maps API → engine mode.
 */
@Injectable({ providedIn: 'root' })
export class AudioResolver {
  private readonly tracksApi = inject(TracksService);
  private readonly history = inject(HistoryService);
  private readonly failedProviders = new Map<number, Set<string>>();

  readonly friendlyError = RESOLVE_FRIENDLY_ERROR;

  resetRetries(): void {
    this.failedProviders.clear();
  }

  forgetRetry(trackId: number): void {
    this.failedProviders.delete(trackId);
  }

  resolvePlayableSource(track: PlayableTrack, callbacks: AudioResolveCallbacks): void {
    if (track.youtubeVideoId) {
      callbacks.onYoutube(track.youtubeVideoId);
      return;
    }

    callbacks.onResolving();
    this.tracksApi.getAudioSource(track.id).subscribe({
      next: (src) => this.handleResponse(track, src, callbacks, false),
      error: (err) => {
        if (callbacks.isStale()) return;
        if (err?.status === 404) this.history.remove(track.id);
        callbacks.onDemo();
      },
    });
  }

  recoverFromPlaybackError(
    track: PlayableTrack,
    failedProvider: 'youtube' | 'stream' | 'demo',
    callbacks: AudioResolveCallbacks,
  ): void {
    const skip = failedProvider === 'stream' ? 'audius' : failedProvider;
    const tried = this.failedProviders.get(track.id) ?? new Set<string>();
    if (tried.has(skip)) {
      this.tryDemoOrNotFound(callbacks);
      return;
    }
    tried.add(skip);
    this.failedProviders.set(track.id, tried);

    callbacks.onResolving();
    this.tracksApi.getAudioSource(track.id, true, skip).subscribe({
      next: (src) => this.handleResponse(track, src, callbacks, true),
      error: () => { if (!callbacks.isStale()) this.tryDemoOrNotFound(callbacks); },
    });
  }

  private handleResponse(
    track: PlayableTrack,
    src: AudioSource,
    callbacks: AudioResolveCallbacks,
    fromRecovery: boolean,
  ): void {
    if (callbacks.isStale()) return;

    if (src.status === 'pending') {
      this.pollPendingSource(track, callbacks, 0, fromRecovery);
      return;
    }

    this.applyResolved(track, mapAudioSourceResponse(src), callbacks);
  }

  private pollPendingSource(
    track: PlayableTrack,
    callbacks: AudioResolveCallbacks,
    attempt: number,
    fromRecovery: boolean,
  ): void {
    const maxAttempts = 8;
    const delayMs = attempt === 0 ? 800 : Math.min(2500, 800 + attempt * 400);
    window.setTimeout(() => {
      if (callbacks.isStale()) return;
      const skip = fromRecovery ? this.lastSkipProvider(track.id) : undefined;
      this.tracksApi.getAudioSource(track.id, false, skip).subscribe({
        next: (retry) => {
          if (callbacks.isStale()) return;
          if (retry.status === 'pending' && attempt + 1 < maxAttempts) {
            this.pollPendingSource(track, callbacks, attempt + 1, fromRecovery);
            return;
          }
          this.applyResolved(track, mapAudioSourceResponse(retry), callbacks);
        },
        error: () => { if (!callbacks.isStale()) callbacks.onDemo(); },
      });
    }, delayMs);
  }

  private applyResolved(
    track: PlayableTrack,
    resolved: ResolvedPlaybackSource,
    callbacks: AudioResolveCallbacks,
  ): void {
    if (callbacks.isStale()) return;

    if (!isPlayableSource(resolved)) {
      if (resolved.status === 'error') {
        callbacks.onDemo();
        return;
      }
      callbacks.onNotFound();
      return;
    }

    if (resolved.provider === 'youtube' && resolved.youtubeVideoId) {
      const updated: PlayableTrack = {
        ...track,
        youtubeVideoId: resolved.youtubeVideoId,
      };
      callbacks.onTrackUpdated(updated);
      callbacks.onYoutube(resolved.youtubeVideoId);
      return;
    }

    if (resolved.provider === 'audius' && resolved.streamUrl) {
      const updated: PlayableTrack = {
        ...track,
        audioUrl: resolved.streamUrl,
      };
      callbacks.onTrackUpdated(updated);
      callbacks.onStream(resolved.streamUrl);
      return;
    }

    callbacks.onDemo();
  }

  private tryDemoOrNotFound(callbacks: AudioResolveCallbacks): void {
    callbacks.onDemo();
  }

  private lastSkipProvider(trackId: number): string | undefined {
    const set = this.failedProviders.get(trackId);
    if (!set?.size) return undefined;
    return [...set].at(-1);
  }
}
