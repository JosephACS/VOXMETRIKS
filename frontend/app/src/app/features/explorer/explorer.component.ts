import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Data Explorer</h1>
      <p>Interactive dataset exploration</p>
    </div>
    <div class="explorer-container">
      <div class="explorer-controls">
        <input type="text" placeholder="Search in dataset..." class="explorer-input"/>
        <button class="explorer-btn">Apply Filters</button>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .explorer-container { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 2rem; }
    .explorer-controls { display: flex; gap: 1rem; }
    .explorer-input { flex: 1; background: var(--vox-surface-light); border: 1px solid var(--vox-border); color: white; padding: 0.75rem 1rem; border-radius: 0.75rem; }
    .explorer-btn { padding: 0.75rem 1.5rem; background: var(--vox-orange); color: var(--vox-black); border: none; border-radius: 0.75rem; font-weight: 600; cursor: pointer; transition: all 200ms; }
    .explorer-btn:hover { transform: translateY(-2px); box-shadow: 0 0 15px rgba(255,140,66,0.3); }
  `]
})
export class ExplorerComponent {}
