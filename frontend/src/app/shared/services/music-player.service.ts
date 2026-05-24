import { Injectable, inject, signal, computed } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { PlayableTrack } from '../models/player.models';
import { CoverArtService } from './cover-art.service';
import { demoAudioUrlForTrack } from '../config/demo-audio.config';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { Track, TopTrack } from '../models/api.models';

const VOLUME_KEY = 'voxmetrik_volume';
const TRACK_KEY = 'voxmetrik_last_track';

@Injectable({ providedIn: 'root' })
export class MusicPlayerService {
  private coverArt = inject(CoverArtService);
  private history = inject(HistoryService);
  private audio = new Audio();
  private queueInternal: PlayableTrack[] = [];
  private queueIndex = 0;

  private tickTimer: ReturnType<typeof setInterval> | null = null;

  currentTrack = signal<PlayableTrack | null>(null);
  isPlaying = signal(false);
  currentTime = signal(0);
  duration = signal(0);
  volume = signal(this.readVolume());
  shuffle = signal(false);
  repeat = signal(false);
  queue = signal<PlayableTrack[]>([]);

  progressPct = computed(() => {
    const d = this.duration();
    return d > 0 ? Math.min(100, (this.currentTime() / d) * 100) : 0;
  });

  /** @deprecated use signals — kept for optional subscriptions */
  state$ = new BehaviorSubject({ playing: false });

  constructor() {
    this.audio.volume = this.volume();
    this.audio.preload = 'metadata';
    this.audio.addEventListener('ended', () => this.onEnded());
    this.audio.addEventListener('loadedmetadata', () => {
      this.duration.set(this.audio.duration || 0);
    });
    this.restoreLastTrack();
    this.startTick();
  }

  fromTrack(t: Track, artistName = '—'): PlayableTrack {
    return {
      id: t.id_track,
      title: t.nombre_track,
      artist: artistName,
      durationMs: t.duration_ms,
      audioUrl: demoAudioUrlForTrack(t.id_track),
      coverGradient: this.coverArt.gradientFor(t.id_track),
      explicit: t.explicit,
    };
  }

  fromTopTrack(t: TopTrack): PlayableTrack {
    return {
      id: t.id_track,
      title: t.nombre_track ?? '—',
      artist: t.nombre_artista ?? '—',
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
    this.audio.pause();
    this.isPlaying.set(false);
    this.state$.next({ playing: false });
  }

  resume() {
    if (!this.currentTrack()) return;
    this.audio.play().catch(() => this.isPlaying.set(false));
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
    this.audio.currentTime = Math.max(0, seconds);
    this.currentTime.set(this.audio.currentTime);
  }

  seekPct(pct: number) {
    const d = this.duration();
    if (d > 0) this.seek((pct / 100) * d);
  }

  setVolume(v: number) {
    const vol = Math.max(0, Math.min(1, v));
    this.volume.set(vol);
    this.audio.volume = vol;
    localStorage.setItem(VOLUME_KEY, String(vol));
  }

  toggleShuffle() { this.shuffle.update((v) => !v); }
  toggleRepeat() { this.repeat.update((v) => !v); }

  formatTime(sec: number): string {
    if (!Number.isFinite(sec)) return '0:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  private loadTrack(track: PlayableTrack, autoplay: boolean) {
    this.currentTrack.set(track);
    this.audio.src = track.audioUrl;
    this.currentTime.set(0);
    this.duration.set(track.durationMs ? track.durationMs / 1000 : 0);
    sessionStorage.setItem(TRACK_KEY, JSON.stringify(track));
    this.history.add({
      id_track: track.id,
      nombre_track: track.title,
      nombre_artista: track.artist,
    });
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
      this.currentTime.set(this.audio.currentTime || 0);
      if (this.audio.duration && !this.duration()) {
        this.duration.set(this.audio.duration);
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
      this.audio.src = track.audioUrl;
    } catch { /* ignore */ }
  }
}
