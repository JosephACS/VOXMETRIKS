import { Injectable, inject, signal, computed } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, map, of, share } from 'rxjs';
import { PlayableTrack } from '../models/player.models';
import { CoverArtService } from './cover-art.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { Track, TopTrack } from '../models/api.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { YoutubeEngineService } from './youtube-engine.service';
import { TrackCoverService } from './track-cover.service';
import { StatsService } from '../../packages/analytics/services/stats.service';
import { formatPlaybackTime, playableFromTopTrack, playableFromTrack } from './player/player-track.factory';
import { PlayerQueue } from './player/player-queue';
import { PlayerPlaybackEngine } from './player/player-playback.engine';
import { PlayerSourceResolver } from './player/player-source.resolver';
import {
  clearPersistedTrack,
  persistCurrentTrack,
  readStoredVolume,
  restorePersistedTrack,
  storeVolume,
} from './player/player-session.storage';
@Injectable({ providedIn: 'root' })
export class MusicPlayerService {
  private static readonly AUTOPLAY_MIN_UPCOMING = 5;
  private static readonly AUTOPLAY_FETCH_SIZE = 24;

  private coverArt = inject(CoverArtService);
  private history = inject(HistoryService);
  private stats = inject(StatsService);
  private tracksSvc = inject(TracksService);
  private yt = inject(YoutubeEngineService);
  private coverSvc = inject(TrackCoverService);
  private readonly queueState = new PlayerQueue();
  private readonly sourceResolver = new PlayerSourceResolver(this.tracksSvc, this.history);
  private playbackToken = 0;
  private autoplayFetch$: Observable<PlayableTrack[]> | null = null;
  /** Cursor para recorrer el catálogo página a página y traer temas frescos. */
  private autoplayPage = 1;
  private readonly engine = new PlayerPlaybackEngine(this.yt, {
    onEnded: () => this.onEnded(),
    onYtPlay: () => this.setPlaying(true),
    onYtPause: () => this.setPlaying(false),
    onYtEnded: () => this.onEnded(),
    onYtError: () => {
      const t = this.currentTrack();
      if (this.engine.isYoutube && t) this.recoverFromYtError(t);
    },
    onDemoMetadata: (d) => this.duration.set(d),
  });
  currentTrack = signal<PlayableTrack | null>(null);
  isPlaying = signal(false);
  currentTime = signal(0);
  duration = signal(0);
  volume = signal(readStoredVolume());
  shuffle = signal(false);
  repeat = signal(false);
  /** Autoplay continuo (estilo Spotify): rellena la cola y sigue al terminar. */
  autoplay = signal(true);
  autoplayLoading = signal(false);
  queue = signal<PlayableTrack[]>([]);
  queueIndex = signal(0);
  expandedOpen = signal(false);
  audioMode = signal<'youtube' | 'demo' | 'loading'>('demo');
  currentCover = signal<string | null>(null);
  /** Pistas que vienen después de la actual (lo que muestra "En cola"). */
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
  /** @deprecated use signals — kept for optional subscriptions */
  state$ = new BehaviorSubject({ playing: false });
  constructor() {
    this.engine.setVolume(this.volume());
    this.restoreLastTrack();
    this.engine.startTick(() => {
      if (!this.isPlaying()) return;
      this.currentTime.set(this.engine.getCurrentTime());
      const d = this.engine.getDuration(this.duration());
      if (d && Math.abs(d - this.duration()) > 1) this.duration.set(d);
    });
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
  playTrack(track: PlayableTrack, queue?: PlayableTrack[]) {
    if (queue?.length) {
      const idx = queue.findIndex((q) => q.id === track.id);
      this.setQueue(queue, idx >= 0 ? idx : 0);
      return;
    }
    this.queueState.setSingle(track);
    this.syncQueueSignal();
    this.loadTrack(track, true);
  }
  toggle() {
    if (!this.currentTrack()) return;
    if (this.isPlaying()) this.pause();
    else this.resume();
  }
  pause() {
    this.engine.pause();
    this.setPlaying(false);
  }
  resume() {
    const track = this.currentTrack();
    if (!track) return;
    if (this.engine.loadedId !== track.id) {
      this.loadTrack(track, true);
      return;
    }
    if (this.engine.isYoutube) this.engine.playYoutube();
    else this.engine.playDemo().then(() => this.setPlaying(true));
    this.setPlaying(true);
  }
  next() {
    const nextTrack = this.queueState.advance(this.shuffle());
    if (nextTrack) {
      this.syncQueueSignal();
      this.loadTrack(nextTrack, true);
    }
  }
  previous() {
    if (this.currentTime() > 3) {
      this.seek(0);
      return;
    }
    const prev = this.queueState.retreat();
    if (prev) {
      this.syncQueueSignal();
      this.loadTrack(prev, true);
    }
  }
  seek(seconds: number) {
    this.currentTime.set(this.engine.seek(seconds));
  }
  seekPct(pct: number) {
    const d = this.duration();
    if (d > 0) this.seek((pct / 100) * d);
  }
  setVolume(v: number) {
    const vol = Math.max(0, Math.min(1, v));
    this.volume.set(vol);
    this.engine.setVolume(vol);
    storeVolume(vol);
  }
  toggleShuffle() { this.shuffle.update((v) => !v); }
  toggleRepeat() { this.repeat.update((v) => !v); }
  toggleAutoplay() { this.autoplay.update((v) => !v); }
  openExpandedView() {
    if (!this.currentTrack()) return;
    this.expandedOpen.set(true);
  }
  closeExpandedView() { this.expandedOpen.set(false); }
  toggleExpandedView() {
    if (!this.currentTrack()) return;
    this.expandedOpen.update((v) => !v);
  }
  clearCover() { this.currentCover.set(null); }
  stopPlayback() {
    this.playbackToken++;
    this.sourceResolver.resetRetries();
    this.engine.stopAll();
    this.queueState.clear();
    this.syncQueueSignal();
    this.currentTrack.set(null);
    this.currentCover.set(null);
    this.setPlaying(false);
    this.currentTime.set(0);
    this.duration.set(0);
    this.audioMode.set('demo');
    this.expandedOpen.set(false);
    clearPersistedTrack();
  }
  formatTime(sec: number): string {
    return formatPlaybackTime(sec);
  }
  private setPlaying(playing: boolean) {
    this.isPlaying.set(playing);
    this.state$.next({ playing });
  }
  private loadTrack(track: PlayableTrack, autoplay: boolean) {
    this.currentTrack.set(track);
    this.currentTime.set(0);
    this.duration.set(track.durationMs ? track.durationMs / 1000 : 0);
    persistCurrentTrack(track);
    this.history.add({
      id_track: track.id,
      nombre_track: track.title,
      nombre_artista: track.artist,
    });
    const token = ++this.playbackToken;
    this.currentCover.set(null);
    this.coverSvc.cover$(track.id).subscribe((url) => {
      if (token === this.playbackToken) this.currentCover.set(url);
    });
    this.sourceResolver.resolve(track, {
      isStale: () => token !== this.playbackToken,
      onLoading: () => this.audioMode.set('loading'),
      onYoutube: (videoId) => this.startYt(track, videoId, autoplay),
      onDemo: () => this.startDemo(track, autoplay),
      onTrackUpdated: (updated) => {
        this.currentTrack.set(updated);
        persistCurrentTrack(updated);
      },
    });
    if (this.autoplay()) this.scheduleAutoplayFill();
  }
  private startYt(track: PlayableTrack, videoId: string, autoplay: boolean) {
    this.audioMode.set('youtube');
    this.engine.markLoaded(track.id, true);
    this.engine.startYoutube(videoId, autoplay);
    if (autoplay) this.setPlaying(true);
  }
  private recoverFromYtError(track: PlayableTrack) {
    const token = this.playbackToken;
    this.sourceResolver.recoverFromYoutubeError(track, {
      isStale: () => token !== this.playbackToken,
      onLoading: () => this.audioMode.set('loading'),
      onYoutube: (videoId) => this.startYt(track, videoId, true),
      onDemo: () => this.startDemo(track, true),
      onTrackUpdated: (updated) => {
        this.currentTrack.set(updated);
        persistCurrentTrack(updated);
      },
    });
  }
  private startDemo(track: PlayableTrack, autoplay: boolean) {
    this.audioMode.set('demo');
    this.engine.startDemo(track.audioUrl, track.id, autoplay).then(() => {
      if (autoplay) this.setPlaying(true);
    });
  }
  private onEnded() {
    if (this.repeat()) {
      this.seek(0);
      this.resume();
      return;
    }
    if (this.queueState.hasNext(this.shuffle())) {
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
    this.setPlaying(false);
    this.currentTime.set(0);
    this.engine.seek(0);
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
      if (added.length) this.syncQueueSignal();
    });
  }
  private continueWithAutoplay() {
    this.autoplayLoading.set(true);
    this.fetchAutoplayCandidates().subscribe({
      next: (tracks) => {
        // Intentamos sumar temas nuevos; si no hay (catálogo corto), seguimos
        // en bucle por la cola existente. Como Spotify: nunca se queda en silencio.
        const added = this.queueState.appendUnique(tracks);
        if (added.length) this.syncQueueSignal();
        this.advanceWrapping();
      },
      // Aunque falle la red, continuamos con lo que ya hay en la cola.
      error: () => this.advanceWrapping(),
      complete: () => this.autoplayLoading.set(false),
    });
  }
  /** Avanza a la siguiente pista; al llegar al final, vuelve al inicio. */
  private advanceWrapping() {
    const nextTrack = this.queueState.advance(this.shuffle());
    if (nextTrack) {
      this.syncQueueSignal();
      this.loadTrack(nextTrack, true);
    } else {
      this.stopAtQueueEnd();
    }
  }
  /**
   * Trae temas frescos recorriendo el catálogo página a página (cada llamada
   * avanza el cursor y vuelve al inicio al final). Así siempre entran canciones
   * nuevas en vez de repetir el mismo set de recomendaciones. Si la API de
   * catálogo falla, cae a top tracks.
   */
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
      finalize(() => { this.autoplayFetch$ = null; }),
      share(),
    );
    return this.autoplayFetch$;
  }
  private restoreLastTrack() {
    const track = restorePersistedTrack();
    if (!track) return;
    this.currentTrack.set(track);
    this.queueState.setSingle(track);
    this.syncQueueSignal();
    this.audioMode.set(track.youtubeVideoId ? 'youtube' : 'demo');
    if (!track.youtubeVideoId) this.engine.primeDemo(track.audioUrl);
  }
}
