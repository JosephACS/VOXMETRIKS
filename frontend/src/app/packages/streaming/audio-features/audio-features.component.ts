import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-audio-features',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Audio Features</h1>
      <p class="page-subtitle">Análisis de características acústicas</p>
    </div>

    <div class="features-info">
      <div class="feature-legend">
        <div *ngFor="let f of featureKeys" class="legend-item">
          <div class="legend-dot" [style.background]="featureColor(f)"></div>
          <span>{{ f }}</span>
        </div>
      </div>
      <p class="info-text">
        Características acústicas disponibles para cada track del catálogo:
        danceability, energy, valence, acousticness, speechiness, instrumentalness y liveness.
      </p>
    </div>

    <div class="features-placeholder">
      <div class="placeholder-icon">⚡</div>
      <h3>Audio Features Explorer</h3>
      <p>Navega a la sección de <strong>Tracks</strong> y selecciona un track para ver su análisis acústico detallado.</p>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .page-subtitle { color: rgba(255,255,255,0.5); margin-top: 0.25rem; }
    .features-info { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 2rem; }
    .feature-legend { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; }
    .legend-item { display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: rgba(255,255,255,0.6); }
    .legend-dot { width: 10px; height: 10px; border-radius: 50%; }
    .info-text { color: rgba(255,255,255,0.5); font-size: 0.875rem; margin: 0; }
    .features-placeholder { text-align: center; padding: 4rem 2rem; background: var(--vox-surface); border: 1px dashed var(--vox-border); border-radius: 0.75rem; }
    .placeholder-icon { font-size: 3rem; margin-bottom: 1rem; }
    .features-placeholder h3 { margin: 0 0 0.5rem; }
    .features-placeholder p { color: rgba(255,255,255,0.4); margin: 0; }
    strong { color: var(--vox-orange, #ff8c42); }
  `],
})
export class AudioFeaturesComponent {
  featureKeys = ['danceability', 'energy', 'valence', 'acousticness', 'speechiness', 'instrumentalness', 'liveness'];

  featureColor(key: string): string {
    const colors: Record<string, string> = {
      danceability: '#ff8c42', energy: '#7c3aed', valence: '#10b981',
      acousticness: '#3b82f6', speechiness: '#f59e0b', instrumentalness: '#ec4899', liveness: '#6366f1',
    };
    return colors[key] ?? '#888';
  }
}
