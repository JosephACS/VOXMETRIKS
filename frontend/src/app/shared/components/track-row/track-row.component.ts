import { Component, Input, DestroyRef, inject, signal, ChangeDetectionStrategy, effect, viewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { DeferVisibleDirective } from '../../directives/defer-visible.directive';
import { MusicPlayerService } from '../../services/music-player.service';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';
import { PlayableTrack } from '../../models/player.models';

@Component({
  selector: 'app-track-row',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, DeferVisibleDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="track-row" appDeferVisible [class.playing]="player.currentTrack()?.id === track.id" (click)="play()">
      <span class="tr-index">{{ index }}</span>
      <button type="button" class="tr-cover" [style.background]="track.coverGradient" (click)="play($event)">
        @if (coverUrl()) {
          <img class="tr-cover-img" [src]="coverUrl()" [alt]="track.title" loading="lazy" (error)="coverUrl.set(null)" />
        } @else {
          <span class="cover-initial tr-cover-letter">{{ coverArt.initialFor(track.title) }}</span>
        }
        <span class="tr-cover-overlay">
          @if (player.currentTrack()?.id === track.id && player.isPlaying()) {
            <span class="eq-bars"><span></span><span></span><span></span></span>
          } @else {
            <svg class="play-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          }
        </span>
      </button>
      <div class="tr-main">
        <a class="tr-title" [routerLink]="['/tracks', track.id]" (click)="$event.stopPropagation()">{{ track.title }}</a>
        <span class="tr-artist">{{ track.artist }}</span>
        @if (energyPct != null) {
          <span class="tr-meta">Energía {{ energyPct }}%</span>
        }
      </div>
      @if (track.explicit) { <span class="tr-explicit" title="Contenido explícito" aria-label="Contenido explícito">E</span> }
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
    .track-row:hover { background: var(--shell-hover); }
    .track-row.playing { background: var(--accent-dim); }
    .tr-index {
      font-size: 0.8125rem;
      color: var(--text-muted);
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
      overflow: hidden;
      padding: 0;
    }
    .tr-cover-letter {
      font-size: 0.9375rem;
      font-weight: 700;
      z-index: 0;
    }
    .tr-cover-img {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      z-index: 0;
    }
    .tr-cover-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0);
      transition: background 0.2s cubic-bezier(0.22, 1, 0.36, 1);
      z-index: 1;
    }
    .track-row:hover .tr-cover-overlay,
    .track-row.playing .tr-cover-overlay {
      background: rgba(0, 0, 0, 0.45);
    }
    .play-icon { opacity: 0; transition: opacity 0.2s cubic-bezier(0.22, 1, 0.36, 1); }
    .track-row:hover .play-icon,
    .track-row.playing .play-icon { opacity: 1; }
    .track-row.playing .tr-cover-letter { opacity: 0.35; }
    .tr-main { min-width: 0; display: flex; flex-direction: column; gap: 0.1rem; }
    .tr-title {
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--text);
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tr-title:hover { text-decoration: underline; }
    .track-row.playing .tr-title { color: #1ed896; }
    .tr-artist {
      font-size: 0.75rem;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tr-meta {
      font-size: 0.6875rem;
      color: rgba(30, 216, 150, 0.75);
      font-family: var(--font-mono, monospace);
    }
    .tr-explicit {
      font-size: 0.625rem;
      font-weight: 700;
      padding: 2px 5px;
      border: 1px solid var(--shell-border-strong);
      border-radius: 3px;
      color: var(--text-muted);
    }
    .tr-pop {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: var(--text-muted);
      min-width: 90px;
    }
    .pop-bar {
      flex: 1;
      height: 4px;
      background: var(--shell-progress-track);
      border-radius: 999px;
      overflow: hidden;
    }
    .pop-fill { height: 100%; background: var(--accent); border-radius: 999px; }
    .tr-duration {
      font-size: 0.8125rem;
      color: var(--text-muted);
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
  coverArt = inject(CoverArtService);
  private coverSvc = inject(TrackCoverService);
  private destroyRef = inject(DestroyRef);
  private defer = viewChild(DeferVisibleDirective);
  private coverRequested = false;

  @Input({ required: true }) track!: PlayableTrack;
  @Input() index = 1;
  @Input() queue: PlayableTrack[] = [];
  @Input() showPopularity = false;
  @Input() popularity?: number | null;
  @Input() energy?: number | null;

  coverUrl = signal<string | null>(null);

  constructor() {
    effect(() => {
      const dir = this.defer();
      if (!dir?.visible() || this.coverRequested) return;
      const id = this.track?.id;
      if (id == null || id < 0) return;
      this.coverRequested = true;
      this.coverSvc.cover$(id)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((url) => this.coverUrl.set(url));
    });
  }

  /** Energy llega en escala 0-1 (Spotify); lo normalizamos a porcentaje 0-100. */
  get energyPct(): number | null {
    if (this.energy == null) return null;
    const pct = this.energy <= 1 ? this.energy * 100 : this.energy;
    return Math.round(pct);
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
