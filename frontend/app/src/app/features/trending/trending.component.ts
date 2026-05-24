import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-trending',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Trending Now</h1>
      <p>Most popular tracks and artists this week</p>
    </div>
    <div class="trending-container">
      <div class="trending-list">
        <div class="trending-item" *ngFor="let i of [1,2,3,4,5]">
          <span class="rank">{{ i }}</span>
          <div class="trending-info">
            <h4>Trending Track {{ i }}</h4>
            <p>Artist Name</p>
          </div>
          <span class="trending-badge">↑ 12%</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .trending-container { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; }
    .trending-list { display: flex; flex-direction: column; }
    .trending-item { display: flex; align-items: center; padding: 1.5rem; border-bottom: 1px solid var(--vox-border); gap: 1rem; transition: all 200ms; }
    .trending-item:last-child { border-bottom: none; }
    .trending-item:hover { background: rgba(255,140,66,0.05); }
    .rank { width: 40px; height: 40px; background: var(--vox-orange); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: var(--vox-black); }
    .trending-info { flex: 1; }
    .trending-info h4 { margin: 0; }
    .trending-info p { margin: 0.25rem 0 0 0; color: rgba(255,255,255,0.6); }
    .trending-badge { color: var(--vox-success); font-weight: 600; }
  `]
})
export class TrendingComponent {}
