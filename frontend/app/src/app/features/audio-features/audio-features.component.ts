import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-audio-features',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Audio Features Analysis</h1>
      <p>Energy, Valence, Danceability, and more</p>
    </div>
    <div class="features-grid">
      <div class="feature-card" *ngFor="let feature of features">
        <h4>{{ feature.name }}</h4>
        <div class="feature-value">{{ feature.value }}</div>
        <div class="feature-description">{{ feature.description }}</div>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .page-header h1 { font-size: 2.25rem; margin-bottom: 0.5rem; }
    .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }
    .feature-card { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1.5rem; }
    .feature-card h4 { margin: 0 0 1rem 0; color: var(--vox-orange); }
    .feature-value { font-size: 2rem; font-weight: bold; margin: 1rem 0; }
    .feature-description { color: rgba(255,255,255,0.6); font-size: 0.875rem; }
  `]
})
export class AudioFeaturesComponent {
  features = [
    { name: 'Energy', value: '6.5', description: 'Intensity and activity' },
    { name: 'Valence', value: '5.8', description: 'Musical positivity' },
    { name: 'Danceability', value: '6.8', description: 'Dance-friendly rhythm' },
    { name: 'Acousticness', value: '4.2', description: 'Acoustic instruments' },
    { name: 'Speechiness', value: '2.1', description: 'Spoken words ratio' },
    { name: 'Liveness', value: '3.9', description: 'Live performance feel' },
  ];
}
