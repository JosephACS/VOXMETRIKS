import { I18nService } from '../../../core/services/i18n.service';
import { isAbortOrOfflineHttpError } from '../../../core/i18n/http-error-keys';
import { Component, DestroyRef, inject, HostListener, effect, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { PlayerController } from '../../../playback-core/player.controller';
import { PlaybackStore } from '../../../playback-core/playback.store';
import { toPlayableFromHistory } from '../../../playback-core/adapters/track.adapter';
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
import { RepeatMode } from '../../models/player.models';

@Component({
  selector: 'app-now-playing-view',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, AddToPlaylistBtnComponent, TranslatePipe],
  templateUrl: './now-playing-view.component.html',
  styleUrls: ['./now-playing-view.component.css'],
})
export class NowPlayingViewComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  readonly controller = inject(PlayerController);
  readonly playback = inject(PlaybackStore);
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
    const inQueue = new Set(this.playback.queue().map((t) => t.id));
    return this.recommended().filter((r) => !inQueue.has(r.id));
  });

  constructor() {
    effect(() => {
      if (typeof document === 'undefined') return;
      document.body.style.overflow = this.playback.expandedOpen() ? 'hidden' : '';
    });
    effect(() => {
      this.playback.queue().forEach((t) => this.resolveCover(t.id));
    });
  }

  ngOnInit() {
    this.playlistsSvc.list().subscribe({
      next: (d) => this.playlists.set((d ?? []).slice(0, 6)),
      error: (err) => {
        if (!isAbortOrOfflineHttpError(err)) {
          console.error('[NowPlayingViewComponent] playlists.list failed', err);
        }
      },
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
        const tracks = (d ?? []).map((t) => this.controller.fromTopTrack(t));
        this.recommended.set(tracks);
        tracks.forEach((t) => this.resolveCover(t.id));
        // Precargar portadas de la cola actual
        this.playback.queue().forEach((t) => this.resolveCover(t.id));
      },
      error: (err) => {
        if (!isAbortOrOfflineHttpError(err)) {
          console.error('[NowPlayingViewComponent] getTopTracks failed', err);
        }
      },
    });
  }

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.playback.expandedOpen()) this.controller.closeExpandedView();
  }

  onProgressClick(e: MouseEvent) {
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    this.controller.seekPct(pct);
  }

  playFromQueue(track: PlayableTrack) {
    this.controller.playTrack(track, this.playback.queue());
  }

  playRecommended(track: PlayableTrack) {
    const q = this.playback.queue();
    const ids = new Set(q.map((t) => t.id));
    const merged = [...q];
    for (const r of this.recommended()) {
      if (!ids.has(r.id)) {
        merged.push(r);
        ids.add(r.id);
      }
    }
    this.controller.playTrack(track, merged.length ? merged : this.recommended());
  }

  playHistoryEntry(h: HistoryEntry) {
    this.controller.playTrack(toPlayableFromHistory(this.coverArt, h));
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
    return this.playback.isCurrentTrack(id);
  }

  removeFromQueue(index: number, e: Event) {
    e.stopPropagation();
    this.controller.removeFromQueue(index);
  }

  canReorderQueue(index: number): boolean {
    return index > this.playback.queueIndex() && this.playback.queue().length > 1;
  }

  moveQueueItem(index: number, direction: -1 | 1, e: Event) {
    e.stopPropagation();
    const target = index + direction;
    const curIdx = this.playback.queueIndex();
    if (index <= curIdx || target <= curIdx) return;
    if (target < 0 || target >= this.playback.queue().length) return;
    this.controller.moveInQueue(index, target);
  }

  repeatTitle(mode: RepeatMode): string {
    if (mode === 'one') return 'player.repeatOne';
    if (mode === 'all') return 'player.repeatAll';
    return 'player.repeatOff';
  }
}
