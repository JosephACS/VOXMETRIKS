/**
 * SpotifyLinkComponent
 * ====================
 * Enlace a Spotify con ícono y ID truncado.
 * Si no hay URL, solo muestra el ID truncado.
 *
 * Uso:
 *   <app-spotify-link [spotifyId]="track.spotify_track_id" [url]="track.url_spotify" />
 */

import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import {
  Component,
  inject,
  Input,
  ChangeDetectionStrategy,
} from '@angular/core';

@Component({
  selector: 'app-spotify-link',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (url) {
      <a
        class="spotify-link"
        [href]="url"
        target="_blank"
        rel="noopener noreferrer"
        [title]="'Abrir en Spotify: ' + (spotifyId ?? '')"
        aria-label="Abrir en Spotify"
      >
        <span class="spotify-dot" aria-hidden="true" [innerHTML]="iconSvg"></span>
        @if (spotifyId && showId) {
          <span class="spotify-id-text font-mono">{{ truncated }}</span>
        }
      </a>
    } @else if (spotifyId && showId) {
      <span class="spotify-id-plain font-mono" [title]="spotifyId">{{ truncated }}</span>
    }
  `,
  styles: [`
    .spotify-link {
      display: inline-flex;
      align-items: center;
      gap: 0.2rem;
      color: var(--color-primary);
      text-decoration: none;
      transition: opacity var(--transition-fast);
    }

    .spotify-link:hover {
      opacity: 0.75;
    }

    .spotify-dot {
      display: inline-flex;
      align-items: center;
      line-height: 0;
    }

    .spotify-dot :deep(svg) { width: 12px; height: 12px; }

    .spotify-id-text,
    .spotify-id-plain {
      font-size: 0.65rem;
      color: var(--color-text-muted);
      background: var(--color-surface-2);
      border-radius: var(--radius-sm);
      padding: 0.1rem 0.25rem;
    }
  `],
})
export class SpotifyLinkComponent {
  private iconRender = inject(IconRenderService);

  @Input() spotifyId: string | null = null;
  @Input() url: string | null = null;
  @Input() showId = true;
  @Input() idLength = 8;

  get truncated(): string {
    if (!this.spotifyId) return '';
    return this.spotifyId.length > this.idLength
      ? `${this.spotifyId.slice(0, this.idLength)}…`
      : this.spotifyId;
  }

  get iconSvg(): SafeHtml {
    return this.iconRender.render('music', 12);
  }
}
