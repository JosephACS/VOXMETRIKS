import { Injectable, inject, signal, computed } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, map, of, share } from 'rxjs';
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
import { RESOLVE_FRIENDLY_ERROR } from '../../playback-core/resolver/resolved-source.model';
import { isGenericDemoAudioUrl } from '../config/demo-audio.config';
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
  private restoredSession = false;
  /** Position to seek after user resumes a restored session (browser autoplay policy). */
  private pendingRestoreTime = 0;

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
  /** @deprecated use repeatMode — true when not off */
  repeat = computed(() => this.repeatMode() !== 'off');
  autoplay = signal(this.prefs.autoplay);
  autoplayLoading = signal(false);
  playbackError = signal<string | null>(null);
  queue = signal<PlayableTrack[]>([]);
  queueIndex = signal(0);
  expandedOpen = signal(false);
  audioMode = signal<'youtube' | 'stream' | 'preview' | 'loading'>('loading');
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

  /** @deprecated use signals */
  state$ = new BehaviorSubject({ playing: false });

  private get engine() {
    return this.playbackEngine.instance;
  }

  constructor() {
    this.playbackEngine.init({
      onEnded: () => this.onEnded(),
      onYtPlay: () => this.setStatus('playing'),
      onYtPause: () => this.setStatus('paused'),
      onYtEnded: () => this.onEnded(),
      onYtError: () => {
        const t = this.currentTrack();
        if (!this.engine.isYoutube || !t) return;
        // Prefer the id the engine was playing — currentTrack may be cleared mid-recovery.
        const playingId = this.engine.currentYoutubeVideoId;
        const withId =
          playingId && t.youtubeVideoId !== playingId
            ? { ...t, youtubeVideoId: playingId }
            : t;
        this.handleAudioFailure(withId, 'youtube');
      },
      onYtBuffering: () => {
        if (this.status() !== 'error') this.setStatus('buffering');
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
    this.queueState.setAll(tracks, startIndex);
    this.syncQueueSignal();
    const track = this.queueState.current;
    if (track) this.loadTrack(track, true);
  }

  playNow(track: PlayableTrack, contextQueue?: PlayableTrack[]) {
    this.playTrack(track, contextQueue);
  }

  playTrack(track: PlayableTrack, queue?: PlayableTrack[]) {
    this.restoredSession = false;
    this.playbackError.set(null);
    if (queue?.length) {
      const idx = queue.findIndex((q) => q.id === track.id);
      if (idx >= 0) {
        this.setQueue(queue, idx);
        return;
      }
    }
    const inQueue = this.queueState.findIndex(track.id);
    if (inQueue >= 0 && this.queueState.items.length > 1) {
      const jumped = this.queueState.jumpTo(inQueue);
      this.syncQueueSignal();
      if (jumped) this.loadTrack(jumped, true);
      return;
    }
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
    this.syncQueueSignal();
    this.schedulePersist();
  }

  addToQueue(track: PlayableTrack): boolean {
    const added = this.queueState.addToEndUnique(track);
    if (added) {
      this.syncQueueSignal();
      this.schedulePersist();
    }
    return added;
  }

  removeFromQueue(index: number): boolean {
    const ok = this.queueState.removeAt(index);
    if (ok) {
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
    this.syncQueueSignal();
    this.schedulePersist();
  }

  clearQueue() {
    const cur = this.currentTrack();
    if (cur) this.queueState.trimToCurrent();
    else this.queueState.clear();
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
    if (this.engine.isYoutube) {
      this.engine.playYoutube();
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

  toggleRepeat() {
    this.cycleRepeat();
  }

  toggleAutoplay() {
    this.autoplay.update((v) => !v);
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
    this.expandedOpen.update((v) => !v);
  }

  clearCover() {
    this.currentCover.set(null);
  }

  stopPlayback() {
    this.history.completeCurrent(this.currentTime() || undefined);
    this.playbackToken++;
    this.audioResolver.cancel();
    this.audioResolver.resetRetries();
    this.engine.stopAll();
    this.queueState.clear();
    this.queueState.clearHistory();
    this.syncQueueSignal();
    this.currentTrack.set(null);
    this.currentCover.set(null);
    this.setStatus('idle');
    this.currentTime.set(0);
    this.duration.set(0);
    this.audioMode.set('loading');
    this.resolvePhase.set('idle');
    this.playbackError.set(null);
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
    this.state$.next({ playing: playing === 'playing' });
  }

  private setPlaying(playing: boolean) {
    this.setStatus(playing ? 'playing' : 'paused');
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
    if (this.persistTimer) clearTimeout(this.persistTimer);
    this.persistTimer = setTimeout(() => this.persistSession(), 300);
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
    // Keep prior cover until a new one resolves — never flash empty placeholder.
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
      onYoutube: (videoId) => this.startYt(track, videoId, shouldAutoplay, options, token),
      onStream: (streamUrl) => this.startStream(track, streamUrl, shouldAutoplay, options, token),
      onPreview: (previewUrl) => this.startPreview(track, previewUrl, shouldAutoplay, options, token),
      onNotFound: () => this.failPlayback(track, token, 'unavailable'),
      onTrackUpdated: (updated) => {
        if (token === this.playbackToken) this.currentTrack.set(updated);
      },
    });

    if (this.autoplay()) this.scheduleAutoplayFill();
    this.schedulePersist();
  }

  private startYt(
    track: PlayableTrack,
    videoId: string,
    autoplay: boolean,
    options: LoadOptions = {},
    token?: number,
  ) {
    if (token != null && token !== this.playbackToken) return;
    this.audioMode.set('youtube');
    this.resolvePhase.set(autoplay ? 'playing' : 'ready');
    this.engine.markLoaded(track.id, true);
    this.engine.startYoutube(videoId, autoplay);
    if (options.restorePosition && options.restorePosition > 0) {
      this.engine.seek(options.restorePosition);
      this.currentTime.set(options.restorePosition);
    }
    if (autoplay) this.setStatus('playing');
    else this.setStatus('paused');
  }

  private startPreview(
    track: PlayableTrack,
    previewUrl: string,
    autoplay: boolean,
    options: LoadOptions = {},
    token?: number,
  ) {
    if (token != null && token !== this.playbackToken) return;
    if (isGenericDemoAudioUrl(previewUrl)) {
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
    this.engine.markLoaded(track.id, false);
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

  private handleAudioFailure(track: PlayableTrack, source: 'youtube' | 'stream' | 'preview') {
    if (source === 'youtube' || source === 'stream') {
      const token = this.playbackToken;
      this.resolvePhase.set('resolving');
      this.audioResolver.recoverFromPlaybackError(track, source, {
        isStale: () => token !== this.playbackToken || this.currentTrack()?.id !== track.id,
        onResolving: () => {
          this.setStatus('loading');
          this.resolvePhase.set('resolving');
        },
        onYoutube: (videoId) => {
          const latest = this.currentTrack();
          const withId = { ...(latest && latest.id === track.id ? latest : track), youtubeVideoId: videoId };
          if (token === this.playbackToken) this.currentTrack.set(withId);
          this.startYt(withId, videoId, true, {}, token);
        },
        onStream: (url) => this.startStream(track, url, true, {}, token),
        onPreview: (url) => this.startPreview(track, url, true, {}, token),
        onNotFound: () => this.failPlayback(track, token, 'unavailable'),
        onTrackUpdated: (updated) => {
          if (token === this.playbackToken) this.currentTrack.set(updated);
        },
      });
      return;
    }
    this.failPlayback(track, this.playbackToken, 'failed');
  }

  private failPlayback(_track: PlayableTrack, token?: number, phase: AudioResolvePhase = 'unavailable') {
    if (token != null && token !== this.playbackToken) return;
    this.history.completeCurrent(this.currentTime() || undefined);
    this.audioMode.set('loading');
    this.resolvePhase.set(phase);
    this.playbackError.set(RESOLVE_FRIENDLY_ERROR);
    this.setStatus('error');
    if (this.queue().length > 1 || this.autoplay()) {
      window.setTimeout(() => {
        if (this.status() === 'error' && (token == null || token === this.playbackToken)) {
          this.next();
        }
      }, 1200);
    }
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
      if (!tracks.length) return;
      const added = this.queueState.appendUnique(tracks);
      if (added.length) {
        this.syncQueueSignal();
        this.schedulePersist();
      }
    });
  }

  private continueWithAutoplay() {
    this.autoplayLoading.set(true);
    this.fetchAutoplayCandidates().subscribe({
      next: (tracks) => {
        const added = this.queueState.appendUnique(tracks);
        if (added.length) {
          this.syncQueueSignal();
          this.schedulePersist();
        }
        this.advanceWrapping();
      },
      error: () => this.advanceWrapping(),
      complete: () => this.autoplayLoading.set(false),
    });
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
    this.autoplayFetch$ = this.tracksSvc.listTracks(page, size).pipe(
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
    } else {
      this.queueState.setSingle(session.track);
    }
    this.syncQueueSignal();

    this.currentTrack.set(session.track);
    this.currentTime.set(session.currentTime ?? 0);
    this.duration.set(session.track.durationMs ? session.track.durationMs / 1000 : 0);
    this.pendingRestoreTime = session.currentTime ?? 0;
    this.setStatus('paused');

    if (session.track.youtubeVideoId) {
      this.audioMode.set('youtube');
      this.resolvePhase.set('ready');
      this.engine.startYoutube(session.track.youtubeVideoId, false);
      this.engine.markLoaded(session.track.id, true);
    } else if (session.track.audioUrl && !isGenericDemoAudioUrl(session.track.audioUrl)) {
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
