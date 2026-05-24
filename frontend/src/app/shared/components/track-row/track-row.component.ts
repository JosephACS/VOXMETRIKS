import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { MusicPlayerService } from '../../services/music-player.service';
import { PlayableTrack } from '../../models/player.models';

@Component({
  selector: 'app-track-row',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent],
  template: `
    <div class="track-row" [class.playing]="isPlaying" (click)="play()">
      <span class="tr-index">{{ index }}</span>
      <button type="button" class="tr-cover" [style.background]="track.coverGradient" (click)="play($event)">
        @if (isPlaying && player.isPlaying()) {
          <span class="eq-bars"><span></span><span></span><span></span></span>
        } @else {
          <svg class="play-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        }
      </button>
      <div class="tr-main">
        <a class="tr-title" [routerLink]="['/tracks', track.id]" (click)="$event.stopPropagation()">{{ track.title }}</a>
        <span class="tr-artist">{{ track.artist }}</span>
      </div>
      @if (track.explicit) { <span class="tr-explicit">E</span> }
      @if (showPopularity && popularity != null) {
        <div class="tr-pop">
          <div class="pop-bar"><div class="pop-fill" [style.width.%]="popularity"></div></div>
          <span>{{ popularity }}</span>
        </div>
      }
      <span class="tr-duration">{{ durationLabel }}</span>
      <div class="tr-actions" (click)="$event.stopPropagation()">
        <app-favorite-btn [trackId]="track.id" size="sm" />
      </div>
    </div>
  `,
  styles: [`
    .track-row {
      display: grid;
      grid-template-columns: 32px 48px 1fr auto auto 48px 40px;
      align-items: center;
      gap: 0.75rem;
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      transition: background 0.15s;
      cursor: pointer;
    }
    .track-row:hover { background: rgba(255,255,255,0.06); }
    .track-row.playing { background: rgba(30,216,150,0.08); }
    .tr-index {
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.4);
      text-align: center;
      font-variant-numeric: tabular-nums;
    }
    .tr-cover {
      width: 40px;
      height: 40px;
      border: none;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      cursor: pointer;
      position: relative;
    }
    .play-icon { opacity: 0; transition: opacity 0.15s; }
    .track-row:hover .play-icon { opacity: 1; }
    .track-row.playing .play-icon { opacity: 0; }
    .tr-main { min-width: 0; display: flex; flex-direction: column; gap: 0.1rem; }
    .tr-title {
      font-size: 0.875rem;
      font-weight: 500;
      color: #fff;
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tr-title:hover { text-decoration: underline; }
    .track-row.playing .tr-title { color: #1ed896; }
    .tr-artist {
      font-size: 0.75rem;
      color: rgba(255,255,255,0.5);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tr-explicit {
      font-size: 0.625rem;
      font-weight: 700;
      padding: 2px 5px;
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 3px;
      color: rgba(255,255,255,0.6);
    }
    .tr-pop {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: rgba(255,255,255,0.55);
      min-width: 90px;
    }
    .pop-bar {
      flex: 1;
      height: 4px;
      background: rgba(255,255,255,0.1);
      border-radius: 999px;
      overflow: hidden;
    }
    .pop-fill { height: 100%; background: #1ed896; border-radius: 999px; }
    .tr-duration {
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.45);
      font-variant-numeric: tabular-nums;
      text-align: right;
    }
    .tr-actions { display: flex; justify-content: flex-end; opacity: 0; transition: opacity 0.15s; }
    .track-row:hover .tr-actions { opacity: 1; }
    .eq-bars {
      display: flex;
      align-items: flex-end;
      gap: 2px;
      height: 14px;
    }
    .eq-bars span {
      width: 3px;
      background: #1ed896;
      animation: eq 0.8s ease-in-out infinite;
    }
    .eq-bars span:nth-child(2) { animation-delay: 0.15s; }
    .eq-bars span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes eq {
      0%, 100% { height: 4px; }
      50% { height: 14px; }
    }
    @media (max-width: 768px) {
      .track-row { grid-template-columns: 28px 44px 1fr 40px; }
      .tr-pop, .tr-explicit, .tr-duration { display: none; }
    }
  `],
})
export class TrackRowComponent {
  player = inject(MusicPlayerService);

  @Input({ required: true }) track!: PlayableTrack;
  @Input() index = 1;
  @Input() queue: PlayableTrack[] = [];
  @Input() showPopularity = false;
  @Input() popularity?: number | null;

  get isPlaying(): boolean {
    return this.player.currentTrack()?.id === this.track.id;
  }

  get durationLabel(): string {
    if (this.track.durationMs) {
      return this.player.formatTime(this.track.durationMs / 1000);
    }
    return '—';
  }

  play(e?: Event) {
    e?.stopPropagation();
    this.player.playTrack(this.track, this.queue.length ? this.queue : undefined);
  }
}
