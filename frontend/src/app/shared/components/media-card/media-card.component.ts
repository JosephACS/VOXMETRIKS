import {
  Component, Input, Output, EventEmitter, inject, OnInit, DestroyRef, signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MusicPlayerService } from '../../services/music-player.service';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';
import { PlayableTrack } from '../../models/player.models';

@Component({
  selector: 'app-media-card',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <article class="media-card" (click)="onCardClick()">
      <div class="media-cover" [class.round]="round" [style.background]="gradient">
        @if (coverUrl()) {
          <img class="cover-img" [src]="coverUrl()" [alt]="title" loading="lazy" (error)="coverUrl.set(null)" />
        } @else {
          <span class="cover-thumb cover-thumb--card">
            <span class="cover-initial">{{ displayInitial }}</span>
          </span>
        }
        @if (badge != null) {
          <span class="media-badge">{{ badge }}</span>
        }
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
        @if (meta) { <span class="media-meta">{{ meta }}</span> }
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
      transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.22s cubic-bezier(0.22, 1, 0.36, 1);
      will-change: transform;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .media-cover.round {
      border-radius: 50%;
    }
    .cover-img {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      z-index: 0;
      animation: coverFade 0.3s ease;
    }
    @keyframes coverFade { from { opacity: 0; } to { opacity: 1; } }
    .media-card:hover .media-cover {
      transform: scale(1.03);
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .media-badge {
      position: absolute;
      top: 0.45rem;
      left: 0.45rem;
      font-size: 0.625rem;
      font-weight: 700;
      font-family: var(--font-mono, monospace);
      padding: 2px 6px;
      border-radius: 999px;
      background: rgba(0, 0, 0, 0.55);
      color: #1ed896;
      backdrop-filter: blur(4px);
      z-index: 1;
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
      transition: opacity 0.22s cubic-bezier(0.22, 1, 0.36, 1), transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
      cursor: pointer;
      box-shadow: 0 8px 16px rgba(0,0,0,0.35);
      z-index: 2;
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
      color: var(--text);
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .media-title:hover { text-decoration: underline; }
    .media-sub {
      display: block;
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .media-meta {
      display: block;
      font-size: 0.6875rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
      font-family: var(--font-mono, monospace);
    }
  `],
})
export class MediaCardComponent implements OnInit {
  private player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);
  private coverSvc = inject(TrackCoverService);
  private destroyRef = inject(DestroyRef);

  @Input({ required: true }) title!: string;
  @Input() subtitle?: string;
  @Input() meta?: string;
  @Input() gradient = 'linear-gradient(135deg, #1ed896, #121212)';
  @Input() link?: string;
  @Input() track?: PlayableTrack;
  @Input() queue: PlayableTrack[] = [];
  /** Etiqueta en la portada; por defecto inicial del título. */
  @Input() coverLabel?: string;
  /** Portada circular (artistas). */
  @Input() round = false;
  /** Badge numérico (p. ej. popularidad). */
  @Input() badge?: number | string | null;
  /** Fuerza/limita la resolución de carátula real por id de track. */
  @Input() coverTrackId?: number;
  @Output() played = new EventEmitter<PlayableTrack>();

  coverUrl = signal<string | null>(null);

  ngOnInit(): void {
    // Carátula real solo para tracks (no para artistas/géneros/playlists).
    const id = this.coverTrackId ?? (this.round ? undefined : this.track?.id);
    if (id == null) return;
    this.coverSvc.cover$(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((url) => this.coverUrl.set(url));
  }

  get displayInitial(): string {
    const label = this.coverLabel ?? this.title;
    return this.round ? this.covers.initialsFor(label) : this.covers.initialFor(label);
  }

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
