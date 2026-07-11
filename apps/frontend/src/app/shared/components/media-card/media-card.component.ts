import {
  Component, Input, Output, EventEmitter, inject, DestroyRef, signal, effect, viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { DeferVisibleDirective } from '../../directives/defer-visible.directive';
import { TrackActionsComponent } from '../track-actions/track-actions.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';
import { PlayableTrack } from '../../models/player.models';

@Component({
  selector: 'app-media-card',
  standalone: true,
  imports: [CommonModule, RouterModule, DeferVisibleDirective, TrackActionsComponent],
  template: `
    <article class="media-card" (click)="onCardClick()">
      <div class="media-cover" appDeferVisible [class.round]="round" [style.background]="gradient">
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
        @if (tag) {
          <span class="media-tag">{{ tag }}</span>
        }
        @if (track) {
          <div class="card-actions" (click)="$event.stopPropagation()">
            <app-track-actions
              [track]="track"
              [queue]="queue"
              [artistId]="track.artistId ?? coverArtistId"
              size="sm"
            />
          </div>
          <button type="button" class="play-overlay" (click)="onPlay($event)" [attr.aria-label]="'Reproducir ' + title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </button>
        }
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
    :host {
      display: block;
      flex: 0 0 184px;
      min-width: 0;
      max-width: 184px;
      scroll-snap-align: start;
    }
    .media-card {
      width: 100%;
      box-sizing: border-box;
      cursor: pointer;
      padding: 0.7rem;
      border-radius: 10px;
      background: transparent;
      transition: var(--motion-transition-interactive);
    }
    .media-card:hover {
      background: var(--shell-hover, rgba(255,255,255,0.055));
    }
    .media-cover {
      position: relative;
      width: 100%;
      aspect-ratio: 1 / 1;
      height: auto;
      border-radius: 7px;
      overflow: hidden;
      box-shadow: 0 6px 18px rgba(0,0,0,0.35);
      transition: box-shadow var(--motion-duration-normal) var(--motion-ease-standard);
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
      box-shadow: 0 12px 28px rgba(0,0,0,0.5);
    }
    .media-badge {
      position: absolute;
      top: 0.45rem;
      right: 0.45rem;
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
    .media-tag {
      position: absolute;
      top: 0.5rem;
      left: 0.5rem;
      right: auto;
      max-width: calc(100% - 1rem);
      font-size: 0.625rem;
      font-weight: 800;
      padding: 3px 9px;
      border-radius: 999px;
      background: #1ed896;
      color: #06150f;
      border: none;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
      z-index: 2;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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
    .card-actions {
      position: absolute;
      top: 0.45rem;
      left: 0.45rem;
      display: flex;
      align-items: center;
      gap: 0.15rem;
      opacity: 0;
      transition: opacity 0.2s;
      z-index: 3;
    }
    .media-card:hover .card-actions { opacity: 1; }
    .media-info { padding: 0.65rem 0.1rem 0; min-width: 0; }
    .media-title {
      display: block;
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--text);
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }
    .media-title:hover { text-decoration: underline; }
    .media-sub {
      display: block;
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
      min-height: 1.0125rem;
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
export class MediaCardComponent {
  private readonly controller = inject(PlayerController);
  private router = inject(Router);
  private covers = inject(CoverArtService);
  private coverSvc = inject(TrackCoverService);
  private destroyRef = inject(DestroyRef);
  private defer = viewChild(DeferVisibleDirective);
  private coverRequested = false;

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
  /** Small pill badge (e.g. Trending, Hit). */
  @Input() tag?: string;
  /** Fuerza/limita la resolución de carátula real por id de track. */
  @Input() coverTrackId?: number;
  /** Fallback: retrato del artista si no hay portada de álbum. */
  @Input() coverArtistId?: number;
  @Output() played = new EventEmitter<PlayableTrack>();

  coverUrl = signal<string | null>(null);

  constructor() {
    effect(() => {
      const dir = this.defer();
      if (!dir?.visible() || this.coverRequested) return;

      const trackId = this.coverTrackId ?? (this.round ? undefined : this.track?.id);
      const artistId = this.coverArtistId ?? this.track?.artistId;

      if (trackId != null) {
        this.coverRequested = true;
        this.coverSvc.bestCover$(trackId, artistId)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe((url) => this.coverUrl.set(url));
      } else if (artistId != null) {
        this.coverRequested = true;
        this.coverSvc.artistCover$(artistId)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe((url) => this.coverUrl.set(url));
      }
    });
  }

  get displayInitial(): string {
    const label = this.coverLabel ?? this.subtitle ?? this.title;
    return this.covers.initialsFor(label);
  }

  onPlay(e: Event) {
    e.stopPropagation();
    if (!this.track) return;
    this.controller.playTrack(this.track, this.queue.length ? this.queue : undefined);
    this.played.emit(this.track);
  }

  onCardClick() {
    if (this.track) {
      this.onPlay(new Event('click'));
      return;
    }
    if (this.link) {
      void this.router.navigateByUrl(this.link);
    }
  }
}
