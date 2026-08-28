import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { SpotifyIntegrationService } from './spotify-integration.service';

@Component({
  selector: 'app-spotify-callback',
  standalone: true,
  template: `
    <main class="spotify-callback" aria-live="polite">
      <div class="spotify-callback__mark" aria-hidden="true">♪</div>
      <p class="spotify-callback__eyebrow">SPOTIFY + VOXMETRIKS</p>
      <h1>{{ failed() ? 'No pudimos conectar Spotify' : 'Terminando la conexión' }}</h1>
      <p>{{ message() }}</p>
    </main>
  `,
  styles: [`
    :host { display: grid; min-height: calc(100dvh - 9rem); place-items: center; }
    .spotify-callback { width: min(32rem, calc(100% - 2rem)); padding: 2rem; text-align: center; border: 1px solid var(--border); border-radius: 1.25rem; background: var(--glass-bg); box-shadow: var(--shadow-md); }
    .spotify-callback__mark { width: 3.25rem; height: 3.25rem; margin: 0 auto 1rem; display: grid; place-items: center; border-radius: 1rem; color: #07120b; background: #1ed760; font-size: 1.5rem; font-weight: 800; }
    .spotify-callback__eyebrow { margin: 0 0 0.55rem; color: #36b76d; font: 700 0.66rem/1 var(--font-mono); letter-spacing: 0.12em; }
    h1 { margin: 0; font-size: clamp(1.35rem, 3vw, 2rem); color: var(--text); }
    p:last-child { margin: 0.75rem auto 0; max-width: 27rem; color: var(--text-muted); line-height: 1.55; }
  `],
})
export class SpotifyCallbackPage implements OnInit {
  private readonly spotify = inject(SpotifyIntegrationService);
  private readonly router = inject(Router);

  readonly failed = signal(false);
  readonly message = signal('Estamos validando el permiso y preparando tus recomendaciones.');

  async ngOnInit(): Promise<void> {
    try {
      await this.spotify.initializeFromCurrentUrl();
      if (!this.spotify.connected()) throw new Error(this.spotify.errorMessage() || 'Spotify no confirmó la conexión.');
      await this.router.navigate(['/recommendations'], { replaceUrl: true });
    } catch (error) {
      this.failed.set(true);
      this.message.set(error instanceof Error ? error.message : 'Vuelve a intentarlo desde Música conectada.');
      window.setTimeout(() => {
        void this.router.navigate(['/settings'], { queryParams: { tab: 'connections' }, replaceUrl: true });
      }, 1800);
    }
  }
}
