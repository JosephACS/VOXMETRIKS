import {
  Component, Input, Output, EventEmitter, inject, DestroyRef, signal, effect, computed, viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DeferVisibleDirective } from '../../directives/defer-visible.directive';
import { CoverMosaicComponent } from '../cover-mosaic/cover-mosaic.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { PlaybackStore } from '../../../playback-core/playback.store';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';
import { PlayableTrack } from '../../models/player.models';

@Component({
  selector: 'app-media-card',
  standalone: true,
  imports: [CommonModule, RouterModule, DeferVisibleDirective, CoverMosaicComponent],
  template: `
    <article
      class="media-card"
      [class.is-current]="isCurrent()"
      [routerLink]="!track && link ? link : null"
      (click)="onCardClick()"
    >
      <div class="media-cover" appDeferVisible [class.round]="round" [style.background]="gradient">
        @if (mosaicTrackIds?.length) {
          <app-cover-mosaic
            [trackIds]="mosaicTrackIds!"
            [seed]="mosaicSeed || title"
          />
        } @else if (coverLoading()) {
          <div class="cover-skel" aria-hidden="true"></div>
        } @else if (coverUrl()) {
          <img class="cover-img" [src]="coverUrl()" [alt]="title" loading="lazy" (error)="onCoverError()" />
        } @else {
          <span class="cover-thumb cover-thumb--card">
            <span class="cover-initial">{{ displayInitial }}</span>
          </span>
        }
        @if (badge != null) {
          <span class="media-badge">{{ badge }}</span>
        }
        @if (track) {
          <button type="button" class="play-overlay" (click)="onPlay($event)" [attr.aria-label]="isCurrent() && playback.isPlaying() ? 'Pausar ' + title : 'Reproducir ' + title">
            @if (isCurrent() && playback.isPlaying()) {
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>
            } @else {
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            }
          </button>
        }
        <svg class="card-waveform" viewBox="0 0 180 34" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 20 C12 7 20 30 34 18 S58 7 72 20 S96 29 110 16 S135 7 150 20 S169 26 180 16" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" opacity=".76" />
        </svg>
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
      flex: 0 0 212px;
      min-width: 0;
      max-width: 212px;
      scroll-snap-align: start;
    }
    .media-card {
      width: 100%;
      box-sizing: border-box;
      cursor: pointer;
      padding: 0;
      border-radius: 18px;
      background: transparent;
      transition:
        transform 260ms cubic-bezier(0.2, 0.82, 0.2, 1),
        filter 220ms ease;
    }
    .media-card:hover {
      transform: translate3d(0, -5px, 0);
    }
    .media-cover {
      position: relative;
      width: 100%;
      aspect-ratio: 1 / 1;
      height: auto;
      border-radius: 18px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.075);
      box-shadow: 0 18px 42px rgba(0,0,0,0.32);
      transition:
        box-shadow 260ms cubic-bezier(0.2, 0.82, 0.2, 1),
        border-color 220ms ease;
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
      transition: transform 720ms cubic-bezier(0.2, 0.82, 0.2, 1), filter 320ms ease;
    }
    .cover-skel {
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, rgba(255,255,255,0.04), rgba(255,255,255,0.12), rgba(255,255,255,0.04));
      background-size: 200% 100%;
      animation: coverShimmer 1.2s ease-in-out infinite;
      z-index: 0;
    }
    @keyframes coverFade { from { opacity: 0; } to { opacity: 1; } }
    @keyframes coverShimmer {
      0% { background-position: 100% 0; }
      100% { background-position: -100% 0; }
    }
    .cover-thumb {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 0;
    }
    .cover-initial {
      font-size: 2rem;
      font-weight: 700;
      color: rgba(255,255,255,0.85);
      letter-spacing: 0.02em;
    }
    .media-card:hover .media-cover {
      border-color: color-mix(in srgb, var(--vx-accent, #e8a33d) 42%, rgba(255,255,255,.12));
      box-shadow: 0 28px 62px rgba(0,0,0,0.5), 0 0 0 1px color-mix(in srgb, var(--vx-accent, #e8a33d) 14%, transparent);
    }
    .media-card.is-current .media-cover {
      border-color: color-mix(in srgb, var(--accent) 58%, rgba(255,255,255,.12));
      box-shadow: 0 28px 62px rgba(0,0,0,.5), 0 0 0 2px color-mix(in srgb, var(--accent) 22%, transparent), 0 0 30px color-mix(in srgb, var(--accent) 16%, transparent);
    }
    .media-card.is-current .card-waveform { opacity: 1; transform: translateY(0); }
    .media-card:hover .cover-img,
    .media-card.is-previewing .cover-img { transform: scale(1.055); }
    .media-card.is-previewing .cover-img { filter: saturate(1.06) brightness(.72); }
    .media-badge {
      position: absolute;
      top: 0.45rem;
      right: 0.45rem;
      font-size: 0.625rem;
      font-weight: 700;
      font-family: var(--font-mono, monospace);
      padding: 2px 6px;
      border-radius: 999px;
      background: rgba(7, 8, 12, 0.68);
      color: #fff;
      backdrop-filter: blur(12px);
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
      background: rgba(7, 8, 12, 0.72);
      color: #fff;
      border: 1px solid rgba(255,255,255,.14);
      backdrop-filter: blur(12px);
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
      background: rgba(247, 245, 252, 0.94);
      color: #090a0f;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.22s cubic-bezier(0.22, 1, 0.36, 1), transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
      cursor: pointer;
      box-shadow: 0 12px 32px rgba(0,0,0,0.42);
      z-index: 5;
    }
    .media-card:hover .play-overlay {
      opacity: 1;
      transform: translateY(0);
    }
    .play-overlay:hover { transform: scale(1.08); background: var(--vx-accent, #e8a33d); }
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
    .preview-stage {
      position: absolute;
      inset: auto 0 0;
      z-index: 3;
      min-height: 48%;
      padding: 1rem 1rem .8rem;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      gap: .6rem;
      color: #fff;
      opacity: 0;
      transform: translateY(8px);
      background: linear-gradient(180deg, transparent, rgba(5,6,10,.82) 68%, rgba(5,6,10,.94));
      transition: opacity 220ms ease, transform 260ms cubic-bezier(.2,.82,.2,1);
      pointer-events: none;
    }
    .media-card.is-preview-armed .preview-stage,
    .media-card.is-previewing .preview-stage {
      opacity: 1;
      transform: translateY(0);
    }
    .preview-stage__eyebrow {
      max-width: calc(100% - 50px);
      font: 650 .58rem/1.2 var(--font-mono, monospace);
      letter-spacing: .1em;
      text-transform: uppercase;
      color: rgba(255,255,255,.76);
    }
    .preview-stage__wave {
      height: 20px;
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .preview-stage__wave i {
      width: 2px;
      height: 5px;
      border-radius: 99px;
      background: var(--vx-accent, #e8a33d);
      opacity: .72;
    }
    .media-card.is-previewing .preview-stage__wave i {
      animation: mediaPreviewWave .72s ease-in-out infinite alternate;
    }
    .preview-stage__wave i:nth-child(2) { animation-delay: -.18s !important; }
    .preview-stage__wave i:nth-child(3) { animation-delay: -.42s !important; }
    .preview-stage__wave i:nth-child(4) { animation-delay: -.08s !important; }
    .preview-stage__wave i:nth-child(5) { animation-delay: -.32s !important; }
    .preview-stage__wave i:nth-child(6) { animation-delay: -.56s !important; }
    @keyframes mediaPreviewWave { to { height: 19px; opacity: 1; } }
    .preview-stage__progress {
      height: 2px;
      overflow: hidden;
      border-radius: 99px;
      background: rgba(255,255,255,.2);
    }
    .preview-stage__progress span {
      display: block;
      width: 100%;
      height: 100%;
      border-radius: inherit;
      background: #fff;
      transform: scaleX(0);
      transform-origin: left;
    }
    .media-card.is-previewing .preview-stage__progress span {
      animation: mediaPreviewProgress 15s linear forwards;
    }
    @keyframes mediaPreviewProgress { to { transform: scaleX(1); } }
    .media-info { padding: 0.8rem 0.15rem 0; min-width: 0; }
    .media-title {
      display: block;
      font-size: 0.94rem;
      font-weight: 650;
      color: var(--text);
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }
    .media-title:hover { color: var(--vx-accent, #e8a33d); }
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
    @media (prefers-reduced-motion: reduce) {
      .media-card,
      .cover-img,
      .preview-stage { transition: none; }
      .media-card:hover { transform: none; }
      .media-card.is-previewing .preview-stage__wave i,
      .media-card.is-previewing .preview-stage__progress span { animation: none; }
    }
  `],
})
export class MediaCardComponent {
  private readonly controller = inject(PlayerController);
  readonly playback = inject(PlaybackStore);
  private covers = inject(CoverArtService);
  private coverSvc = inject(TrackCoverService);
  private destroyRef = inject(DestroyRef);
  private defer = viewChild(DeferVisibleDirective);
  private coverRequested = false;

  @Input({ required: true }) title!: string;
  @Input() subtitle?: string;
  @Input() meta?: string;
  @Input() gradient = 'linear-gradient(135deg, #e8a33d, #17130c)';
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
  /** URL ya resuelta (p. ej. smart home cache) — evita round-trip inicial. */
  @Input() imageUrl?: string | null;
  /** Spotify-style mosaic from track ids (playlists / albums). */
  @Input() mosaicTrackIds?: number[];
  @Input() mosaicSeed?: string | number;
  @Output() played = new EventEmitter<PlayableTrack>();

  coverUrl = signal<string | null>(null);
  coverLoading = signal(false);
  readonly isCurrent = computed(() => !!this.track && this.playback.isCurrentTrack(this.track.id));

  constructor() {
    effect(() => {
      const preset = this.imageUrl;
      if (preset) {
        this.coverUrl.set(preset);
        this.coverLoading.set(false);
      }

      if (this.mosaicTrackIds?.length) {
        this.coverLoading.set(false);
        return;
      }

      const dir = this.defer();
      if (!dir?.visible() || this.coverRequested) return;

      const trackId = this.coverTrackId ?? (this.round ? undefined : this.track?.id);
      const artistId = this.coverArtistId ?? this.track?.artistId;

      if (trackId != null) {
        this.coverRequested = true;
        if (!preset) this.coverLoading.set(true);
        this.coverSvc.bestCover$(trackId, artistId)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe((url) => {
            if (url) this.coverUrl.set(url);
            this.coverLoading.set(false);
          });
      } else if (artistId != null) {
        this.coverRequested = true;
        if (!preset) this.coverLoading.set(true);
        this.coverSvc.artistCover$(artistId)
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe((url) => {
            if (url) this.coverUrl.set(url);
            this.coverLoading.set(false);
          });
      }
    });
  }

  get displayInitial(): string {
    const label = this.coverLabel ?? this.subtitle ?? this.title;
    return this.covers.initialsFor(label);
  }

  onCoverError() {
    this.coverUrl.set(null);
    this.coverLoading.set(false);
  }

  onPlay(e: Event) {
    e.stopPropagation();
    if (!this.track) return;
    if (this.isCurrent()) {
      this.controller.toggle();
      this.played.emit(this.track);
      return;
    }
    this.controller.playTrack(this.track, this.queue.length ? this.queue : undefined);
    this.played.emit(this.track);
  }

  onCardClick() {
    // Link-only cards navigate via [routerLink] on the article.
    if (this.track) {
      this.onPlay(new Event('click'));
    }
  }

}
