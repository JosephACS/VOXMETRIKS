import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, catchError, finalize, map, of, share } from 'rxjs';
import { PlayableTrack, PlaybackStatus, RepeatMode, AudioResolvePhase } from '../models/player.models';
import { CoverArtService } from './cover-art.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { ListenStatsService } from '../../packages/streaming/services/listen-stats.service';
import { Track, TopTrack } from '../models/api.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { TrackCoverService } from './track-cover.service';
import { StatsService } from '../../packages/analytics/services/stats.service';
import { formatPlaybackTime, playableFromTopTrack, playableFromTrack } from './player/player-track.factory';
import { QueueManager } from '../../playback-core/queue.manager';
import { PlaybackEngine } from '../../playback-core/playback.engine';
import { cycleRepeatMode } from '../../playback-core/playback-history';
import { AudioResolver } from '../../playback-core/resolver/audio.resolver';
import { isGenericToneAudioUrl } from '../config/generic-tone-audio.config';
import {
  clearPersistedSession,
  persistPlaybackSession,
  readPlaybackPrefs,
  restorePlaybackSession,
  storePlaybackPrefs,
  storeVolume,
} from './player/player-session.storage';

interface LoadOptions {
  skipHistory?: boolean;
  restorePosition?: number;
  userInitiated?: boolean;
}

@Injectable({ providedIn: 'root' })
export class MusicPlayerService {
  private static readonly AUTOPLAY_MIN_UPCOMING = 5;
  private static readonly AUTOPLAY_FETCH_SIZE = 24;

  private coverArt = inject(CoverArtService);
  private history = inject(HistoryService);
  private listenStats = inject(ListenStatsService);
  private stats = inject(StatsService);
  private tracksSvc = inject(TracksService);
  private coverSvc = inject(TrackCoverService);
  private readonly queueState = inject(QueueManager);
  private readonly playbackEngine = inject(PlaybackEngine);
  private readonly audioResolver = inject(AudioResolver);
  private playbackToken = 0;
  private autoplayFetch$: Observable<PlayableTrack[]> | null = null;
  private autoplayPage = 1;
  private persistTimer: ReturnType<typeof setTimeout> | null = null;
  private skipNoticeTimer: ReturnType<typeof setTimeout> | null = null;
  private restoredSession = false;
  /** Position to seek after user resumes a restored session (browser autoplay policy). */
  private pendingRestoreTime = 0;
  /** Track ids that failed during the current playback run. Autoplay will not retry them. */
  private readonly unavailableTrackIds = new Set<number>();
  /** Keeps queue semantics after failed items are removed and only one item remains. */
  private queuePlaybackActive = false;

  private readonly prefs = readPlaybackPrefs();

  status = signal<PlaybackStatus>('idle');
  currentTrack = signal<PlayableTrack | null>(null);
  isPlaying = signal(false);
  currentTime = signal(0);
  duration = signal(0);
  volume = signal(this.prefs.volume);
  muted = signal(this.prefs.muted);
  shuffle = signal(this.prefs.shuffle);
  repeatMode = signal<RepeatMode>(this.prefs.repeatMode);
  autoplay = signal(this.prefs.autoplay);
  autoplayLoading = signal(false);
  playbackError = signal<string | null>(null);
  /** Brief, non-blocking notice for a one-off track that has no source. */
  skipNotice = signal<string | null>(null);
  /** True when every track in a finite queue failed to resolve. */
  queueExhausted = signal(false);
  queue = signal<PlayableTrack[]>([]);
  queueIndex = signal(0);
  expandedOpen = signal(false);
  audioMode = signal<'spotify' | 'stream' | 'preview' | 'loading'>('loading');
  /** User-facing resolve lifecycle (idle → resolving → ready/playing | unavailable). */
  resolvePhase = signal<AudioResolvePhase>('idle');
  currentCover = signal<string | null>(null);

  upcomingQueue = computed(() => {
    const q = this.queue();
    const idx = this.queueIndex();
    if (!q.length || idx >= q.length - 1) return [];
    return q.slice(idx + 1);
  });

  progressPct = computed(() => {
    const d = this.duration();
    return d > 0 ? Math.min(100, (this.currentTime() / d) * 100) : 0;
  });

  private get engine() {
    return this.playbackEngine.instance;
  }

  constructor() {
    this.playbackEngine.init({
      onEnded: () => this.onEnded(),
      onSpotifyPlay: () => this.setStatus('playing'),
      onSpotifyPause: () => {
        if (this.status() !== 'loading') this.setStatus('paused');
      },
      onSpotifyEnded: () => this.onEnded(),
      onSpotifyError: () => {
        const track = this.currentTrack();
        if (track && this.engine.isSpotify) this.fallbackFromSpotify(track, this.playbackToken);
      },
      onDemoMetadata: (d) => this.duration.set(d),
      onDemoWaiting: () => {
        if (this.status() === 'playing' || this.status() === 'loading') {
          this.setStatus('buffering');
        }
      },
      onDemoPlaying: () => {
        if (this.status() === 'buffering') this.setStatus('playing');
      },
    });
    this.applyVolume();
    this.restoreSession();
    this.engine.startTick(() => this.onTick());
  }

  fromTrack(t: Track, artistName?: string): PlayableTrack {
    return playableFromTrack(this.coverArt, t, artistName);
  }

  fromTopTrack(t: TopTrack): PlayableTrack {
    return playableFromTopTrack(this.coverArt, t);
  }

  setQueue(tracks: PlayableTrack[], startIndex = 0) {
    this.queuePlaybackActive = tracks.length > 1;
    this.queueExhausted.set(false);
    this.unavailableTrackIds.clear();
    this.clearSkipNotice();
    this.queueState.setAll(tracks, startIndex);
    this.syncQueueSignal();
    this.schedulePersist();
    const track = this.queueState.current;
    if (track) this.loadTrack(track, true);
  }

  playNow(track: PlayableTrack, contextQueue?: PlayableTrack[]) {
    this.playTrack(track, contextQueue);
  }

  playTrack(track: PlayableTrack, queue?: PlayableTrack[]) {
    this.restoredSession = false;
    this.playbackError.set(null);
    this.queueExhausted.set(false);
    this.unavailableTrackIds.clear();
    this.clearSkipNotice();
    if (queue?.length) {
      this.queuePlaybackActive = queue.length > 1;
      const idx = queue.findIndex((q) => q.id === track.id);
      if (idx >= 0) {
        this.setQueue(queue, idx);
        return;
      }
    }
    const inQueue = this.queueState.findIndex(track.id);
    if (inQueue >= 0 && this.queueState.items.length > 1) {
      this.queuePlaybackActive = true;
      const jumped = this.queueState.jumpTo(inQueue);
      this.syncQueueSignal();
      if (jumped) this.loadTrack(jumped, true);
      return;
    }
    this.queuePlaybackActive = false;
    this.queueState.setSingle(track);
    this.syncQueueSignal();
    this.loadTrack(track, true);
  }

  playNextInQueue(track: PlayableTrack) {
    if (!this.currentTrack()) {
      this.playTrack(track);
      return;
    }
    this.queueState.insertNext(track);
    this.queuePlaybackActive = this.queueState.items.length > 1;
    this.syncQueueSignal();
    this.schedulePersist();
  }

  addToQueue(track: PlayableTrack): boolean {
    const added = this.queueState.addToEndUnique(track);
    if (added) {
      this.queuePlaybackActive = this.queueState.items.length > 1;
      this.syncQueueSignal();
      this.schedulePersist();
    }
    return added;
  }

  removeFromQueue(index: number): boolean {
    const ok = this.queueState.removeAt(index);
    if (ok) {
      this.queuePlaybackActive = this.queueState.items.length > 1;
      this.syncQueueSignal();
      this.schedulePersist();
    }
    return ok;
  }

  moveInQueue(from: number, to: number): boolean {
    const ok = this.queueState.move(from, to);
    if (ok) {
      this.syncQueueSignal();
      this.schedulePersist();
    }
    return ok;
  }

  clearPendingQueue() {
    if (!this.currentTrack()) return;
    this.queueState.trimToCurrent();
    this.queuePlaybackActive = false;
    this.syncQueueSignal();
    this.schedulePersist();
  }

  toggle() {
    if (!this.currentTrack()) return;
    if (this.isPlaying()) this.pause();
    else this.resume();
  }

  pause() {
    this.engine.pause();
    this.setStatus('paused');
    this.history.pauseListenClock();
    this.schedulePersist();
  }

  resume() {
    this.restoredSession = false;
    const track = this.currentTrack();
    if (!track) return;
    this.playbackError.set(null);
    if (this.engine.loadedId !== track.id) {
      const restorePos = this.pendingRestoreTime;
      this.pendingRestoreTime = 0;
      this.loadTrack(track, true, { userInitiated: true, restorePosition: restorePos || undefined });
      return;
    }
    if (this.engine.isSpotify) {
      void this.engine.playSpotify().then((ok) => {
        if (!ok) this.fallbackFromSpotify(track, this.playbackToken);
      });
      if (this.pendingRestoreTime > 0) {
        const pos = this.pendingRestoreTime;
        this.pendingRestoreTime = 0;
        this.engine.seek(pos);
        this.currentTime.set(pos);
      }
    } else {
      this.engine.playDemo().then(() => this.setStatus('playing'));
    }
    this.setStatus('playing');
  }

  next() {
    this.playbackError.set(null);
    const nextTrack = this.queueState.advance(this.shuffle(), this.repeatMode());
    if (nextTrack) {
      this.syncQueueSignal();
      this.loadTrack(nextTrack, true);
      return;
    }
    if (this.autoplay()) this.continueWithAutoplay();
    else this.stopAtQueueEnd();
  }

  previous() {
    if (this.currentTime() > 3) {
      this.seek(0);
      return;
    }
    const prev = this.queueState.previousFromHistory();
    if (prev) {
      const idx = this.queueState.findIndex(prev.id);
      if (idx >= 0) this.queueState.jumpTo(idx);
      this.syncQueueSignal();
      this.loadTrack(prev, true, { skipHistory: true });
      return;
    }
    this.seek(0);
  }

  seek(seconds: number) {
    this.currentTime.set(this.engine.seek(seconds));
    // Seeking must not inflate listened_ms — pause the wall-clock sample gap.
    this.history.pauseListenClock();
    this.schedulePersist();
  }

  seekPct(pct: number) {
    const d = this.duration();
    if (d > 0) this.seek((pct / 100) * d);
  }

  setVolume(v: number) {
    const vol = Math.max(0, Math.min(1, v));
    this.volume.set(vol);
    if (this.muted()) this.muted.set(false);
    this.applyVolume();
    storeVolume(vol);
    this.persistPrefs();
  }

  toggleMute() {
    this.muted.update((m) => !m);
    this.applyVolume();
    this.persistPrefs();
  }

  toggleShuffle() {
    this.shuffle.update((v) => !v);
    this.persistPrefs();
  }

  cycleRepeat() {
    this.repeatMode.update((m) => cycleRepeatMode(m));
    this.persistPrefs();
  }

  setRepeatMode(mode: RepeatMode) {
    this.repeatMode.set(mode);
    this.persistPrefs();
  }

  retryCurrent() {
    const track = this.currentTrack();
    if (!track) return;
    this.playbackError.set(null);
    this.audioResolver.forgetRetry(track.id);
    this.loadTrack(track, true, { userInitiated: true });
  }

  openExpandedView() {
    if (!this.currentTrack()) return;
    this.expandedOpen.set(true);
  }

  closeExpandedView() {
    this.expandedOpen.set(false);
  }

  toggleExpandedView() {
    if (!this.currentTrack()) return;
    if (this.expandedOpen()) this.closeExpandedView();
    else this.openExpandedView();
  }

  clearCover() {
    this.currentCover.set(null);
  }

  stopPlayback() {
    this.cancelScheduledPersist();
    this.clearSkipNotice();
    this.unavailableTrackIds.clear();
    this.history.completeCurrent(this.currentTime() || undefined);
    this.playbackToken++;
    this.audioResolver.cancel();
    this.audioResolver.resetRetries();
    this.engine.stopAll();
    this.queueState.clear();
    this.queueState.clearHistory();
    this.queuePlaybackActive = false;
    this.syncQueueSignal();
    this.currentTrack.set(null);
    this.currentCover.set(null);
    this.setStatus('idle');
    this.currentTime.set(0);
    this.duration.set(0);
    this.audioMode.set('loading');
    this.resolvePhase.set('idle');
    this.playbackError.set(null);
    this.queueExhausted.set(false);
    this.expandedOpen.set(false);
    this.pendingRestoreTime = 0;
    clearPersistedSession();
  }

  formatTime(sec: number): string {
    return formatPlaybackTime(sec);
  }

  private onTick() {
    if (!this.isPlaying()) return;
    this.listenStats.tick(1);
    this.currentTime.set(this.engine.getCurrentTime());
    const d = this.engine.getDuration(this.duration());
    if (d && Math.abs(d - this.duration()) > 1) this.duration.set(d);
    if (this.currentTime() > 0 && this.currentTime() % 5 < 0.3) this.schedulePersist();
    this.history.updateProgress(this.currentTime(), this.duration());
  }

  private setStatus(playing: PlaybackStatus) {
    this.status.set(playing);
    this.isPlaying.set(playing === 'playing');
  }

  private applyVolume() {
    const effective = this.muted() ? 0 : this.volume();
    this.engine.setVolume(effective);
  }

  private persistPrefs() {
    storePlaybackPrefs({
      volume: this.volume(),
      muted: this.muted(),
      shuffle: this.shuffle(),
      repeatMode: this.repeatMode(),
      autoplay: this.autoplay(),
    });
  }

  private schedulePersist() {
    this.cancelScheduledPersist();
    this.persistTimer = setTimeout(() => {
      this.persistTimer = null;
      this.persistSession();
    }, 300);
  }

  private cancelScheduledPersist() {
    if (this.persistTimer === null) return;
    clearTimeout(this.persistTimer);
    this.persistTimer = null;
  }

  private persistSession() {
    persistPlaybackSession({
      track: this.currentTrack(),
      queue: [...this.queue()],
      queueIndex: this.queueIndex(),
      currentTime: this.currentTime(),
      playbackHistory: this.queueState.playHistory.toArray(),
    });
  }

  private loadTrack(track: PlayableTrack, autoplay: boolean, options: LoadOptions = {}) {
    const leaving = this.currentTrack();
    if (leaving && leaving.id !== track.id && !options.skipHistory) {
      this.queueState.recordPlayed(leaving);
    }

    // Close prior listen session before opening a new one — including reload
    // of the same track (repeat-one / replay) so each play gets a fresh event key.
    if (leaving) {
      this.history.completeCurrent(this.currentTime() || undefined);
    }

    // Cancel prior resolve so a late response cannot swap the current track.
    if (leaving) this.audioResolver.cancel(leaving.id);
    this.audioResolver.cancel(track.id);

    this.engine.stopAll();
    this.currentTrack.set(track);
    this.currentCover.set(null);
    if (!options.restorePosition) this.currentTime.set(0);
    this.duration.set(track.durationMs ? track.durationMs / 1000 : 0);
    this.playbackError.set(null);
    this.setStatus('loading');
    this.resolvePhase.set('resolving');
    this.audioMode.set('loading');

    this.history.add({
      id_track: track.id,
      nombre_track: track.title,
      nombre_artista: track.artist,
    });

    const token = ++this.playbackToken;
    this.coverSvc.cover$(track.id).subscribe((url) => {
      if (token === this.playbackToken && url) this.currentCover.set(url);
    });

    const shouldAutoplay = autoplay && options.userInitiated !== false && !this.restoredSession;
    this.restoredSession = false;

    this.audioResolver.resolvePlayableSource(track, {
      isStale: () => token !== this.playbackToken || this.currentTrack()?.id !== track.id,
      onResolving: () => {
        this.audioMode.set('loading');
        this.setStatus('loading');
        this.resolvePhase.set('resolving');
      },
      onSpotify: (uri) => this.startSpotify(track, uri, shouldAutoplay, options, token),
      onStream: (streamUrl) => this.startStream(track, streamUrl, shouldAutoplay, options, token),
      onPreview: (previewUrl) => this.startPreview(track, previewUrl, shouldAutoplay, options, token),
      onNotFound: (reason) => this.failPlayback(track, token, 'unavailable', reason),
      onTrackUpdated: (updated) => {
        if (token === this.playbackToken) this.currentTrack.set(updated);
      },
    });

    if (this.autoplay()) this.scheduleAutoplayFill();
    this.schedulePersist();
  }

  private startSpotify(
    track: PlayableTrack,
    uri: string,
    autoplay: boolean,
    options: LoadOptions = {},
    token?: number,
  ): void {
    if (token != null && token !== this.playbackToken) return;
    const spotifyTrackId = uri.split(':').pop() || track.spotifyTrackId;
    const updated = { ...track, spotifyTrackId, spotifyUri: uri };
    this.currentTrack.set(updated);
    this.audioMode.set('spotify');
    this.resolvePhase.set(autoplay ? 'playing' : 'ready');
    this.playbackError.set(null);
    this.engine.markSpotifyLoaded(track.id);
    void this.engine.startSpotify(uri, track.id, autoplay).then((ok) => {
      if (token != null && token !== this.playbackToken) return;
      if (!ok) {
        this.fallbackFromSpotify(updated, token ?? this.playbackToken);
        return;
      }
      if (options.restorePosition && options.restorePosition > 0) {
        this.currentTime.set(this.engine.seek(options.restorePosition));
      }
      this.setStatus(autoplay ? 'playing' : 'paused');
    });
  }

  private fallbackFromSpotify(track: PlayableTrack, token: number): void {
    if (token !== this.playbackToken || this.currentTrack()?.id !== track.id || this.audioMode() !== 'spotify') return;
    this.failPlayback(track, token, 'unavailable');
  }

  private startPreview(
    track: PlayableTrack,
    previewUrl: string,
    autoplay: boolean,
    options: LoadOptions = {},
    token?: number,
  ) {
    if (token != null && token !== this.playbackToken) return;
    if (isGenericToneAudioUrl(previewUrl)) {
      this.failPlayback(track, token, 'unavailable');
      return;
    }
    this.audioMode.set('preview');
    this.resolvePhase.set(autoplay ? 'playing' : 'ready');
    this.playbackError.set(null);
    this.engine.startDemo(previewUrl, track.id, autoplay).then((ok) => {
      if (token != null && token !== this.playbackToken) return;
      if (!ok && autoplay) {
        this.handleAudioFailure(track, 'preview');
        return;
      }
      if (options.restorePosition && options.restorePosition > 0) {
        this.currentTime.set(this.engine.seek(options.restorePosition));
      }
      this.setStatus(autoplay ? 'playing' : 'paused');
    });
  }

  private startStream(
    track: PlayableTrack,
    streamUrl: string,
    autoplay: boolean,
    options: LoadOptions = {},
    token?: number,
  ) {
    if (token != null && token !== this.playbackToken) return;
    this.audioMode.set('stream');
    this.resolvePhase.set(autoplay ? 'playing' : 'ready');
    this.engine.startDemo(streamUrl, track.id, autoplay).then((ok) => {
      if (token != null && token !== this.playbackToken) return;
      if (!ok && autoplay) {
        this.handleAudioFailure(track, 'stream');
        return;
      }
      if (options.restorePosition && options.restorePosition > 0) {
        this.currentTime.set(this.engine.seek(options.restorePosition));
      }
      this.setStatus(autoplay ? 'playing' : 'paused');
    });
  }

  private handleAudioFailure(track: PlayableTrack, source: 'spotify' | 'stream' | 'preview') {
    if (source === 'spotify') {
      const token = this.playbackToken;
      this.resolvePhase.set('resolving');
      this.audioResolver.recoverFromPlaybackError(track, source, {
        isStale: () => token !== this.playbackToken || this.currentTrack()?.id !== track.id,
        onResolving: () => {
          this.setStatus('loading');
          this.resolvePhase.set('resolving');
        },
        onStream: (url) => this.startStream(track, url, true, {}, token),
        onPreview: (url) => this.startPreview(track, url, true, {}, token),
        onNotFound: (reason) => this.failPlayback(track, token, 'unavailable', reason),
        onTrackUpdated: (updated) => {
          if (token === this.playbackToken) this.currentTrack.set(updated);
        },
      });
      return;
    }
    this.failPlayback(track, this.playbackToken, 'failed');
  }

  private failPlayback(
    track: PlayableTrack,
    token?: number,
    phase: AudioResolvePhase = 'unavailable',
    reason = 'source_unavailable',
  ) {
    if (token != null && token !== this.playbackToken) return;

    this.unavailableTrackIds.add(track.id);
    this.history.completeCurrent(this.currentTime() || undefined);
    this.engine.stopAll();
    this.audioMode.set('loading');
    this.resolvePhase.set(phase);
    // A missing source is a recoverable navigation event, never a blocking
    // player error. The queue path immediately loads the next item below.
    this.playbackError.set(null);

    const currentIndex = this.queueState.findIndex(track.id);
    const queueContext = this.queuePlaybackActive;
    const hasUpcoming =
      currentIndex >= 0 && currentIndex < this.queueState.items.length - 1;

    console.info('[MusicPlayer] skipped unavailable track', {
      trackId: track.id,
      title: track.title,
      artist: track.artist,
      reason,
      queue: queueContext,
    });

    if (hasUpcoming) {
      this.queueState.removeAt(currentIndex);
      this.syncQueueSignal();
      this.schedulePersist();
      const nextTrack = this.queueState.current;
      if (nextTrack) {
        this.queueExhausted.set(false);
        this.loadTrack(nextTrack, true, { skipHistory: true });
        return;
      }
    }

    // Autoplay may still provide a fresh candidate after the finite queue is
    // exhausted. Failed ids are filtered out so an empty catalog cannot loop.
    if (this.autoplay() && queueContext && currentIndex >= 0) {
      this.queueState.removeAt(currentIndex);
      this.syncQueueSignal();
      this.schedulePersist();
      this.continueWithAutoplay(true);
      return;
    }

    if (queueContext) {
      this.showQueueExhausted();
      return;
    }

    // One-off search: preserve the selected cover and show only a short toast.
    this.setStatus('paused');
    this.currentTime.set(0);
    this.showSkipNotice('Canción no disponible');
  }

  private showSkipNotice(message: string): void {
    if (this.skipNoticeTimer !== null) clearTimeout(this.skipNoticeTimer);
    this.skipNotice.set(message);
    this.skipNoticeTimer = setTimeout(() => {
      this.skipNoticeTimer = null;
      this.skipNotice.set(null);
    }, 2800);
  }

  private clearSkipNotice(): void {
    if (this.skipNoticeTimer !== null) {
      clearTimeout(this.skipNoticeTimer);
      this.skipNoticeTimer = null;
    }
    this.skipNotice.set(null);
  }

  private showQueueExhausted(): void {
    this.queueState.clear();
    this.queuePlaybackActive = false;
    this.syncQueueSignal();
    this.currentTrack.set(null);
    this.currentCover.set(null);
    this.currentTime.set(0);
    this.duration.set(0);
    this.audioMode.set('loading');
    this.resolvePhase.set('unavailable');
    this.playbackError.set(null);
    this.queueExhausted.set(true);
    this.setStatus('paused');
    this.showSkipNotice('No pudimos reproducir ninguna canción de esta cola');
    this.schedulePersist();
  }

  private onEnded() {
    this.history.completeCurrent(this.currentTime() || this.duration());
    if (this.repeatMode() === 'one') {
      const track = this.currentTrack();
      this.seek(0);
      // New listening session after each completion (new event key).
      if (track) {
        this.history.add({
          id_track: track.id,
          nombre_track: track.title,
          nombre_artista: track.artist,
        });
      }
      this.resume();
      return;
    }
    if (this.queueState.hasNext(this.shuffle(), this.repeatMode())) {
      this.next();
      return;
    }
    if (this.autoplay()) {
      this.continueWithAutoplay();
      return;
    }
    this.stopAtQueueEnd();
  }

  private stopAtQueueEnd() {
    this.engine.pause();
    this.setStatus('paused');
    this.currentTime.set(0);
    this.engine.seek(0);
    this.schedulePersist();
  }

  private syncQueueSignal() {
    this.queue.set([...this.queueState.items]);
    this.queueIndex.set(this.queueState.currentIndex);
  }

  private scheduleAutoplayFill() {
    if (!this.autoplay()) return;
    if (this.queueState.upcomingCount() >= MusicPlayerService.AUTOPLAY_MIN_UPCOMING) return;
    this.fetchAutoplayCandidates().subscribe((tracks) => {
      const candidates = this.filterUnavailable(tracks);
      if (!candidates.length) return;
      const added = this.queueState.appendUnique(candidates);
      if (added.length) {
        this.syncQueueSignal();
        this.schedulePersist();
      }
    });
  }

  private continueWithAutoplay(afterUnavailable = false) {
    this.autoplayLoading.set(true);
    this.fetchAutoplayCandidates().subscribe({
      next: (tracks) => {
        const added = this.queueState.appendUnique(this.filterUnavailable(tracks));
        if (added.length) {
          this.syncQueueSignal();
          this.schedulePersist();
        }
        if (added.length || !afterUnavailable) this.advanceWrapping();
        else this.showQueueExhausted();
      },
      error: () => (afterUnavailable ? this.showQueueExhausted() : this.advanceWrapping()),
      complete: () => this.autoplayLoading.set(false),
    });
  }

  private filterUnavailable(tracks: PlayableTrack[]): PlayableTrack[] {
    return tracks.filter((track) => !this.unavailableTrackIds.has(track.id));
  }

  private advanceWrapping() {
    const nextTrack = this.queueState.advance(this.shuffle(), 'all');
    if (nextTrack) {
      this.syncQueueSignal();
      this.loadTrack(nextTrack, true);
    } else {
      this.stopAtQueueEnd();
    }
  }

  private fetchAutoplayCandidates(): Observable<PlayableTrack[]> {
    if (this.autoplayFetch$) return this.autoplayFetch$;
    const size = MusicPlayerService.AUTOPLAY_FETCH_SIZE;
    const page = this.autoplayPage;
    // Autoplay should prefer already verified sources. Catalog pages themselves
    // request the complete Spotify-backed dataset and resolve Deezer on demand.
    this.autoplayFetch$ = this.tracksSvc.listTracks(
      page,
      size,
      undefined,
      undefined,
      undefined,
      true,
    ).pipe(
      map((res) => {
        const total = res?.total ?? 0;
        const totalPages = Math.max(1, Math.ceil(total / size));
        this.autoplayPage = page >= totalPages ? 1 : page + 1;
        return (res?.items ?? []).map((t) => this.fromTrack(t));
      }),
      catchError(() =>
        this.stats.getTopTracks(size).pipe(
          map((rows) => (rows ?? []).map((t) => this.fromTopTrack(t))),
          catchError(() => of([] as PlayableTrack[])),
        ),
      ),
      finalize(() => {
        this.autoplayFetch$ = null;
      }),
      share(),
    );
    return this.autoplayFetch$;
  }

  private restoreSession() {
    const session = restorePlaybackSession();
    if (!session?.track) {
      this.setStatus('idle');
      return;
    }

    this.restoredSession = true;
    if (session.queue.length) {
      this.queueState.restoreQueue(session.queue, session.queueIndex, session.playbackHistory ?? []);
      this.queuePlaybackActive = session.queue.length > 1;
    } else {
      this.queueState.setSingle(session.track);
      this.queuePlaybackActive = false;
    }
    this.syncQueueSignal();

    const restoredTrack = session.track;
    this.currentTrack.set(restoredTrack);
    this.currentCover.set(null);
    this.coverSvc.cover$(restoredTrack.id).subscribe((url) => {
      if (this.currentTrack()?.id === restoredTrack.id && url) this.currentCover.set(url);
    });
    this.currentTime.set(session.currentTime ?? 0);
    this.duration.set(session.track.durationMs ? session.track.durationMs / 1000 : 0);
    this.pendingRestoreTime = session.currentTime ?? 0;
    this.setStatus('paused');

    if (session.track.spotifyUri) {
      this.audioMode.set('spotify');
      this.resolvePhase.set('ready');
      this.engine.markSpotifyLoaded(session.track.id);
    } else if (session.track.audioUrl && !isGenericToneAudioUrl(session.track.audioUrl)) {
      this.audioMode.set('stream');
      this.resolvePhase.set('ready');
      this.engine.primeDemo(session.track.audioUrl);
      if (session.currentTime > 0) {
        this.engine.startDemo(session.track.audioUrl, session.track.id, false).then(() => {
          this.currentTime.set(this.engine.seek(session.currentTime));
          this.pendingRestoreTime = 0;
        });
      }
    } else {
      this.audioMode.set('loading');
      this.resolvePhase.set('idle');
    }
  }
}
