import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MusicPlayerService } from '../../services/music-player.service';
import { PlayableTrack } from '../../models/player.models';

@Component({
  selector: 'app-media-card',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <article class="media-card" (click)="onCardClick()">
      <div class="media-cover" [style.background]="gradient">
        <button type="button" class="play-overlay" (click)="onPlay($event)" [attr.aria-label]="'Reproducir ' + title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        </button>
      </div>
      <div class="media-info">
        @if (link) {
          <a class="media-title" [routerLink]="link" (click)="$event.stopPropagation()">{{ title }}</a>
        } @else {
          <span class="media-title">{{ title }}</span>
        }
        @if (subtitle) { <span class="media-sub">{{ subtitle }}</span> }
      </div>
    </article>
  `,
  styles: [`
    .media-card {
      flex: 0 0 150px;
      scroll-snap-align: start;
      cursor: pointer;
    }
    .media-cover {
      position: relative;
      aspect-ratio: 1;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      will-change: transform;
    }
    .media-card:hover .media-cover {
      transform: scale(1.03);
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .play-overlay {
      position: absolute;
      right: 0.65rem;
      bottom: 0.65rem;
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: none;
      background: #1ed896;
      color: #000;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.2s, transform 0.2s;
      cursor: pointer;
      box-shadow: 0 8px 16px rgba(0,0,0,0.35);
    }
    .media-card:hover .play-overlay {
      opacity: 1;
      transform: translateY(0);
    }
    .play-overlay:hover { transform: scale(1.08); background: #fff; }
    .media-info { padding: 0.65rem 0.15rem 0; min-width: 0; }
    .media-title {
      display: block;
      font-size: 0.875rem;
      font-weight: 600;
      color: #fff;
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .media-title:hover { text-decoration: underline; }
    .media-sub {
      display: block;
      font-size: 0.75rem;
      color: rgba(255,255,255,0.5);
      margin-top: 0.2rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `],
})
export class MediaCardComponent {
  private player = inject(MusicPlayerService);

  @Input({ required: true }) title!: string;
  @Input() subtitle?: string;
  @Input() gradient = 'linear-gradient(135deg, #1ed896, #121212)';
  @Input() link?: string;
  @Input() track?: PlayableTrack;
  @Input() queue: PlayableTrack[] = [];
  @Output() played = new EventEmitter<PlayableTrack>();

  onPlay(e: Event) {
    e.stopPropagation();
    if (!this.track) return;
    this.player.playTrack(this.track, this.queue.length ? this.queue : undefined);
    this.played.emit(this.track);
  }

  onCardClick() {
    if (this.track) this.onPlay(new Event('click'));
  }
}
