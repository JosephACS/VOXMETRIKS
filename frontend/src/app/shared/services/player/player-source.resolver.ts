import { PlayableTrack } from '../../models/player.models';
import { TracksService } from '../../../packages/streaming/services/tracks.service';
import { HistoryService } from '../../../packages/streaming/services/history.service';

export type PlaybackMode = 'youtube' | 'demo' | 'loading';

export interface SourceResolverCallbacks {
  onLoading: () => void;
  onYoutube: (videoId: string) => void;
  onDemo: () => void;
  onTrackUpdated: (track: PlayableTrack) => void;
  isStale: () => boolean;
}

/** Resolves YouTube vs demo audio for a track. */
export class PlayerSourceResolver {
  private readonly ytRetried = new Set<number>();

  constructor(
    private readonly tracksApi: TracksService,
    private readonly history: HistoryService,
  ) {}

  resetRetries(): void {
    this.ytRetried.clear();
  }

  forgetRetry(trackId: number): void {
    this.ytRetried.delete(trackId);
  }

  resolve(track: PlayableTrack, callbacks: SourceResolverCallbacks): void {
    if (track.youtubeVideoId) {
      callbacks.onYoutube(track.youtubeVideoId);
      return;
    }

    callbacks.onLoading();
    this.tracksApi.getAudioSource(track.id).subscribe({
      next: (src) => {
        if (callbacks.isStale()) return;
        if (src.status === 'pending') {
          window.setTimeout(() => {
            if (callbacks.isStale()) return;
            this.tracksApi.getAudioSource(track.id).subscribe({
              next: (retry) => this.applySource(track, retry, callbacks),
              error: () => { if (!callbacks.isStale()) callbacks.onDemo(); },
            });
          }, 1200);
          return;
        }
        this.applySource(track, src, callbacks);
      },
      error: (err) => {
        if (callbacks.isStale()) return;
        if (err?.status === 404) this.history.remove(track.id);
        callbacks.onDemo();
      },
    });
  }

  recoverFromYoutubeError(track: PlayableTrack, callbacks: SourceResolverCallbacks): void {
    if (this.ytRetried.has(track.id)) {
      callbacks.onDemo();
      return;
    }
    this.ytRetried.add(track.id);
    callbacks.onLoading();
    this.tracksApi.getAudioSource(track.id, true).subscribe({
      next: (src) => {
        if (callbacks.isStale()) return;
        if (src.status === 'ok' && src.youtube_video_id && src.youtube_video_id !== track.youtubeVideoId) {
          const updated = { ...track, youtubeVideoId: src.youtube_video_id };
          callbacks.onTrackUpdated(updated);
          callbacks.onYoutube(src.youtube_video_id);
        } else {
          callbacks.onDemo();
        }
      },
      error: () => { if (!callbacks.isStale()) callbacks.onDemo(); },
    });
  }

  private applySource(
    track: PlayableTrack,
    src: { status: string; youtube_video_id?: string | null },
    callbacks: SourceResolverCallbacks,
  ): void {
    if (callbacks.isStale()) return;
    if (src.status === 'ok' && src.youtube_video_id) {
      const updated = { ...track, youtubeVideoId: src.youtube_video_id };
      callbacks.onTrackUpdated(updated);
      callbacks.onYoutube(src.youtube_video_id);
    } else {
      callbacks.onDemo();
    }
  }
}
