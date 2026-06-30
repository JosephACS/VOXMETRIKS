import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, HostListener, effect, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MusicPlayerService } from '../../services/music-player.service';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';
import { PlaylistsService } from '../../../packages/streaming/services/playlists.service';
import { HistoryService } from '../../../packages/streaming/services/history.service';
import { StatsService } from '../../../packages/analytics/services/stats.service';
import { PlaylistSummary, HistoryEntry } from '../../models/api.models';
import { PlayableTrack } from '../../models/player.models';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { AddToPlaylistBtnComponent } from '../add-to-playlist-btn/add-to-playlist-btn.component';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { demoAudioUrlForTrack } from '../../config/demo-audio.config';

@Component({
  selector: 'app-now-playing-view',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, AddToPlaylistBtnComponent, TranslatePipe],
  templateUrl: './now-playing-view.component.html',
  styleUrls: ['./now-playing-view.component.css'],
})
export class NowPlayingViewComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  player = inject(MusicPlayerService);
  private coverArt = inject(CoverArtService);
  private trackCover = inject(TrackCoverService);
  private playlistsSvc = inject(PlaylistsService);
  private historySvc = inject(HistoryService);
  private statsSvc = inject(StatsService);
  private destroyRef = inject(DestroyRef);

  playlists = signal<PlaylistSummary[]>([]);
  history = signal<HistoryEntry[]>([]);
  recommended = signal<PlayableTrack[]>([]);
  /** Resolved real cover URLs per track id (same source the player uses). */
  private covers = signal<Record<number, string>>({});

  /** Recomendadas que aún no están en la cola del reproductor. */
  recommendedVisible = computed(() => {
    const inQueue = new Set(this.player.queue().map((t) => t.id));
    return this.recommended().filter((r) => !inQueue.has(r.id));
  });

  constructor() {
    effect(() => {
      if (typeof document === 'undefined') return;
      document.body.style.overflow = this.player.expandedOpen() ? 'hidden' : '';
    });
    effect(() => {
      this.player.queue().forEach((t) => this.resolveCover(t.id));
    });
  }

  ngOnInit() {
    this.playlistsSvc.list().subscribe({
      next: (d) => this.playlists.set((d ?? []).slice(0, 6)),
      error: (err) => console.error('[NowPlayingViewComponent] playlists.list failed', err),
    });
    this.historySvc.history$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((h) => {
        const recent = h.slice(0, 6);
        this.history.set(recent);
        recent.forEach((entry) => this.resolveCover(entry.id_track));
      });
    this.statsSvc.getTopTracks(12).subscribe({
      next: (d) => {
        const tracks = (d ?? []).map((t) => this.player.fromTopTrack(t));
        this.recommended.set(tracks);
        tracks.forEach((t) => this.resolveCover(t.id));
        // Precargar portadas de la cola actual
        this.player.queue().forEach((t) => this.resolveCover(t.id));
      },
      error: (err) => console.error('[NowPlayingViewComponent] getTopTracks failed', err),
    });
  }

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.player.expandedOpen()) this.player.closeExpandedView();
  }

  onProgressClick(e: MouseEvent) {
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    this.player.seekPct(pct);
  }

  playFromQueue(track: PlayableTrack) {
    this.player.playTrack(track, this.player.queue());
  }

  playRecommended(track: PlayableTrack) {
    const q = this.player.queue();
    const ids = new Set(q.map((t) => t.id));
    const merged = [...q];
    for (const r of this.recommended()) {
      if (!ids.has(r.id)) {
        merged.push(r);
        ids.add(r.id);
      }
    }
    this.player.playTrack(track, merged.length ? merged : this.recommended());
  }

  playHistoryEntry(h: HistoryEntry) {
    const track: PlayableTrack = {
      id: h.id_track,
      title: h.nombre_track,
      artist: h.nombre_artista ?? '—',
      audioUrl: demoAudioUrlForTrack(h.id_track),
      coverGradient: this.coverArt.gradientFor(h.id_track),
    };
    this.player.playTrack(track);
  }

  coverFor(id: number): string {
    return this.coverArt.gradientFor(id);
  }

  /** Real cover URL for a track id (or null → gradient placeholder). */
  coverUrl(id: number): string | null {
    return this.covers()[id] ?? null;
  }

  /** Resolve a real cover via the same service the player uses; cache per id. */
  private resolveCover(id: number): void {
    if (!id || id < 0 || this.covers()[id] !== undefined) return;
    this.trackCover
      .cover$(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((url) => {
        if (url) this.covers.update((m) => ({ ...m, [id]: url }));
      });
  }

  isCurrent(id: number): boolean {
    return this.player.currentTrack()?.id === id;
  }
}
