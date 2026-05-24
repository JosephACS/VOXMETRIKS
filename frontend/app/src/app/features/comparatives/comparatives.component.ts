import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-comparatives',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Comparative Analysis</h1>
      <p>Compare artists, tracks, and genres</p>
    </div>
    <div class="comparison-grid">
      <div class="comparison-card">
        <h3>Artist Comparison</h3>
        <p>Compare popularity and metrics</p>
      </div>
      <div class="comparison-card">
        <h3>Genre Comparison</h3>
        <p>Audio features by genre</p>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .comparison-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; }
    .comparison-card { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1.5rem; }
  `]
})
export class ComparativesComponent {}
