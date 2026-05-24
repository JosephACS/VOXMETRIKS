import { Component, HostListener, effect, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MusicPlayerService } from '../../services/music-player.service';
import { CoverArtService } from '../../services/cover-art.service';
import { PlaylistsService } from '../../../packages/streaming/services/playlists.service';
import { HistoryService } from '../../../packages/streaming/services/history.service';
import { StatsService } from '../../../packages/analytics/services/stats.service';
import { PlaylistSummary, HistoryEntry } from '../../models/api.models';
import { PlayableTrack } from '../../models/player.models';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { demoAudioUrlForTrack } from '../../config/demo-audio.config';

@Component({
  selector: 'app-now-playing-view',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, TranslatePipe],
  templateUrl: './now-playing-view.component.html',
  styleUrls: ['./now-playing-view.component.css'],
})
export class NowPlayingViewComponent implements OnInit {
  player = inject(MusicPlayerService);
  private coverArt = inject(CoverArtService);
  private playlistsSvc = inject(PlaylistsService);
  private historySvc = inject(HistoryService);
  private statsSvc = inject(StatsService);

  playlists = signal<PlaylistSummary[]>([]);
  history = signal<HistoryEntry[]>([]);
  recommended = signal<PlayableTrack[]>([]);

  constructor() {
    effect(() => {
      if (typeof document === 'undefined') return;
      document.body.style.overflow = this.player.expandedOpen() ? 'hidden' : '';
    });
  }

  ngOnInit() {
    this.playlistsSvc.list().subscribe({
      next: (d) => this.playlists.set((d ?? []).slice(0, 6)),
      error: () => {},
    });
    this.historySvc.history$.subscribe((h) => this.history.set(h.slice(0, 6)));
    this.statsSvc.getTopTracks(12).subscribe({
      next: (d) => {
        const tracks = (d ?? []).map((t) => this.player.fromTopTrack(t));
        this.recommended.set(tracks);
      },
      error: () => {},
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
    const q = this.player.queue();
    this.player.playTrack(track, q.length ? q : [track]);
  }

  playRecommended(track: PlayableTrack) {
    this.player.playTrack(track, this.recommended());
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

  isCurrent(id: number): boolean {
    return this.player.currentTrack()?.id === id;
  }
}
