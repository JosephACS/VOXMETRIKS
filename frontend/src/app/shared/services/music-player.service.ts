import { Injectable, inject, signal, computed } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { PlayableTrack } from '../models/player.models';
import { CoverArtService } from './cover-art.service';
import { demoAudioUrlForTrack } from '../config/demo-audio.config';
import { primaryArtistName } from '../utils/artist.util';
import { displayTrackTitle, displayTrackSubtitle } from '../utils/track-display.util';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { Track, TopTrack } from '../models/api.models';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { YoutubeEngineService } from './youtube-engine.service';

const VOLUME_KEY = 'voxmetrik_volume';
const TRACK_KEY = 'voxmetrik_last_track';

@Injectable({ providedIn: 'root' })
export class MusicPlayerService {
  private coverArt = inject(CoverArtService);
  private history = inject(HistoryService);
  private tracksApi = inject(TracksService);
  private yt = inject(YoutubeEngineService);
  private audio = new Audio();
  private queueInternal: PlayableTrack[] = [];
  private queueIndex = 0;

  /** True when playback is currently driven by the YouTube engine. */
  private usingYt = false;
  /** Track id currently loaded into an engine (guards restore + resume). */
  private engineLoadedTrackId: number | null = null;
  /** Monotonic token to drop stale async audio-source resolutions. */
  private playbackToken = 0;

  private tickTimer: ReturnType<typeof setInterval> | null = null;

  currentTrack = signal<PlayableTrack | null>(null);
  isPlaying = signal(false);
  currentTime = signal(0);
  duration = signal(0);
  volume = signal(this.readVolume());
  shuffle = signal(false);
  repeat = signal(false);
  queue = signal<PlayableTrack[]>([]);
  expandedOpen = signal(false);
  /** Active playback source for the current track. */
  audioMode = signal<'youtube' | 'demo' | 'loading'>('demo');

  progressPct = computed(() => {
    const d = this.duration();
    return d > 0 ? Math.min(100, (this.currentTime() / d) * 100) : 0;
  });

  /** @deprecated use signals — kept for optional subscriptions */
  state$ = new BehaviorSubject({ playing: false });

  constructor() {
    this.audio.volume = this.volume();
    this.audio.preload = 'metadata';
    this.audio.addEventListener('ended', () => {
      if (!this.usingYt) this.onEnded();
    });
    this.audio.addEventListener('loadedmetadata', () => {
      if (!this.usingYt) this.duration.set(this.audio.duration || 0);
    });

    this.yt.setVolume(this.volume() * 100);
    this.yt.onPlay = () => {
      if (this.usingYt) { this.isPlaying.set(true); this.state$.next({ playing: true }); }
    };
    this.yt.onPause = () => {
      if (this.usingYt) { this.isPlaying.set(false); this.state$.next({ playing: false }); }
    };
    this.yt.onEnded = () => {
      if (this.usingYt) this.onEnded();
    };
    this.yt.onError = () => {
      // YouTube playback failed for this track → fall back to demo audio.
      const t = this.currentTrack();
      if (this.usingYt && t) this.startDemo(t, true);
    };

    this.restoreLastTrack();
    this.startTick();
  }

  fromTrack(t: Track, artistName?: string): PlayableTrack {
    const artist = t.nombre_artista?.trim()
      ? primaryArtistName(t.nombre_artista)
      : (artistName?.trim() || '—');
    return {
      id: t.id_track,
      title: displayTrackTitle(t.nombre_track),
      artist: displayTrackSubtitle(artist, t.nombre_genero, t.id_track),
      durationMs: t.duration_ms,
      audioUrl: demoAudioUrlForTrack(t.id_track),
      coverGradient: this.coverArt.gradientFor(t.id_track),
      explicit: t.explicit,
    };
  }

  fromTopTrack(t: TopTrack): PlayableTrack {
    return {
      id: t.id_track,
      title: displayTrackTitle(t.nombre_track),
      artist: displayTrackSubtitle(t.nombre_artista, undefined, t.id_track),
      audioUrl: demoAudioUrlForTrack(t.id_track),
      coverGradient: this.coverArt.gradientFor(t.id_track),
    };
  }

  setQueue(tracks: PlayableTrack[], startIndex = 0) {
    this.queueInternal = tracks;
    this.queueIndex = Math.max(0, Math.min(startIndex, tracks.length - 1));
    this.queue.set([...tracks]);
    if (tracks.length) this.loadTrack(tracks[this.queueIndex], true);
  }

  playTrack(track: PlayableTrack, queue?: PlayableTrack[]) {
    if (queue?.length) {
      const idx = queue.findIndex((q) => q.id === track.id);
      this.setQueue(queue, idx >= 0 ? idx : 0);
      return;
    }
    this.queueInternal = [track];
    this.queueIndex = 0;
    this.queue.set([track]);
    this.loadTrack(track, true);
  }

  toggle() {
    if (!this.currentTrack()) return;
    if (this.isPlaying()) this.pause();
    else this.resume();
  }

  pause() {
    if (this.usingYt) this.yt.pause();
    else this.audio.pause();
    this.isPlaying.set(false);
    this.state$.next({ playing: false });
  }

  resume() {
    const track = this.currentTrack();
    if (!track) return;
    // After a session restore nothing is loaded into an engine yet → reload.
    if (this.engineLoadedTrackId !== track.id) {
      this.loadTrack(track, true);
      return;
    }
    if (this.usingYt) {
      this.yt.play();
    } else {
      this.audio.play().catch(() => this.isPlaying.set(false));
    }
    this.isPlaying.set(true);
    this.state$.next({ playing: true });
  }

  next() {
    if (!this.queueInternal.length) return;
    if (this.shuffle()) {
      this.queueIndex = Math.floor(Math.random() * this.queueInternal.length);
    } else {
      this.queueIndex = (this.queueIndex + 1) % this.queueInternal.length;
    }
    this.loadTrack(this.queueInternal[this.queueIndex], true);
  }

  previous() {
    if (this.currentTime() > 3) {
      this.seek(0);
      return;
    }
    if (!this.queueInternal.length) return;
    this.queueIndex = (this.queueIndex - 1 + this.queueInternal.length) % this.queueInternal.length;
    this.loadTrack(this.queueInternal[this.queueIndex], true);
  }

  seek(seconds: number) {
    const target = Math.max(0, seconds);
    if (this.usingYt) {
      this.yt.seekTo(target);
      this.currentTime.set(target);
    } else {
      this.audio.currentTime = target;
      this.currentTime.set(this.audio.currentTime);
    }
  }

  seekPct(pct: number) {
    const d = this.duration();
    if (d > 0) this.seek((pct / 100) * d);
  }

  setVolume(v: number) {
    const vol = Math.max(0, Math.min(1, v));
    this.volume.set(vol);
    this.audio.volume = vol;
    this.yt.setVolume(vol * 100);
    localStorage.setItem(VOLUME_KEY, String(vol));
  }

  toggleShuffle() { this.shuffle.update((v) => !v); }
  toggleRepeat() { this.repeat.update((v) => !v); }

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

  formatTime(sec: number): string {
    if (!Number.isFinite(sec)) return '0:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  private loadTrack(track: PlayableTrack, autoplay: boolean) {
    this.currentTrack.set(track);
    this.currentTime.set(0);
    this.duration.set(track.durationMs ? track.durationMs / 1000 : 0);
    sessionStorage.setItem(TRACK_KEY, JSON.stringify(track));
    this.history.add({
      id_track: track.id,
      nombre_track: track.title,
      nombre_artista: track.artist,
    });

    const token = ++this.playbackToken;
    if (track.youtubeVideoId) {
      this.startYt(track, track.youtubeVideoId, autoplay);
      return;
    }
    this.audioMode.set('loading');
    // Resolve the real (YouTube) source lazily, then play it. Until it
    // resolves we keep the UI responsive; on failure we fall back to demo.
    this.tracksApi.getAudioSource(track.id).subscribe({
      next: (src) => {
        if (token !== this.playbackToken) return; // user moved on
        if (src.status === 'ok' && src.youtube_video_id) {
          track.youtubeVideoId = src.youtube_video_id;
          this.currentTrack.set({ ...track });
          sessionStorage.setItem(TRACK_KEY, JSON.stringify(track));
          this.startYt(track, src.youtube_video_id, autoplay);
        } else {
          this.startDemo(track, autoplay);
        }
      },
      error: () => {
        if (token === this.playbackToken) this.startDemo(track, autoplay);
      },
    });
  }

  private startYt(track: PlayableTrack, videoId: string, autoplay: boolean) {
    this.usingYt = true;
    this.audioMode.set('youtube');
    this.engineLoadedTrackId = track.id;
    this.audio.pause();
    this.yt.load(videoId, autoplay);
    if (autoplay) {
      this.isPlaying.set(true);
      this.state$.next({ playing: true });
    }
  }

  private startDemo(track: PlayableTrack, autoplay: boolean) {
    this.usingYt = false;
    this.audioMode.set('demo');
    this.engineLoadedTrackId = track.id;
    this.yt.stop();
    this.audio.src = track.audioUrl;
    if (autoplay) {
      this.audio.play().then(() => {
        this.isPlaying.set(true);
        this.state$.next({ playing: true });
      }).catch(() => this.isPlaying.set(false));
    }
  }

  private onEnded() {
    if (this.repeat()) {
      this.seek(0);
      this.resume();
      return;
    }
    this.next();
  }

  private startTick() {
    if (this.tickTimer) clearInterval(this.tickTimer);
    this.tickTimer = setInterval(() => {
      if (!this.isPlaying()) return;
      if (this.usingYt) {
        this.currentTime.set(this.yt.getCurrentTime() || 0);
        const d = this.yt.getDuration();
        if (d && Math.abs(d - this.duration()) > 1) this.duration.set(d);
      } else {
        this.currentTime.set(this.audio.currentTime || 0);
        if (this.audio.duration && !this.duration()) {
          this.duration.set(this.audio.duration);
        }
      }
    }, 250);
  }

  private readVolume(): number {
    const v = parseFloat(localStorage.getItem(VOLUME_KEY) ?? '0.85');
    return Number.isFinite(v) ? v : 0.85;
  }

  private restoreLastTrack() {
    try {
      const raw = sessionStorage.getItem(TRACK_KEY);
      if (!raw) return;
      const track = JSON.parse(raw) as PlayableTrack;
      this.currentTrack.set(track);
      this.queueInternal = [track];
      this.queue.set([track]);
      this.audioMode.set(track.youtubeVideoId ? 'youtube' : 'demo');
      if (!track.youtubeVideoId) this.audio.src = track.audioUrl;
    } catch { /* ignore */ }
  }
}
