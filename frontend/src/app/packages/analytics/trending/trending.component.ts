import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../services/stats.service';
import { TopTrack } from '../../../shared/models/api.models';

@Component({
  selector: 'app-trending',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Trending</h1>
      <p class="page-subtitle">Tracks más populares del catálogo</p>
    </div>

    <div *ngIf="isLoading()" class="skeleton-list">
      <div *ngFor="let s of skeletonRows" class="skeleton-row"></div>
    </div>

    <div *ngIf="!isLoading() && tracks().length" class="trending-list">
      <div *ngFor="let t of tracks(); let i = index" class="trending-item">
        <span class="rank">{{ i + 1 }}</span>
        <div class="track-info">
          <div class="track-name">{{ t.nombre_track ?? '—' }}</div>
          <div class="track-artist">{{ t.nombre_artista ?? '—' }}</div>
        </div>
        <div class="popularity-bar">
          <div class="bar-fill" [style.width.%]="t.popularity ?? 0"></div>
          <span class="bar-label">{{ t.popularity ?? '—' }}</span>
        </div>
      </div>
    </div>

    <div *ngIf="!isLoading() && !tracks().length && !hasError()" class="empty-state">
      <p>No hay datos de trending disponibles.</p>
    </div>

    <div *ngIf="hasError()" class="error-state">
      <p>⚠️ Error al cargar trending. Verifica que FastAPI esté corriendo.</p>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .page-subtitle { color: rgba(255,255,255,0.5); margin-top: 0.25rem; }
    .trending-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .trending-item { display: flex; align-items: center; gap: 1rem; background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1rem 1.25rem; }
    .rank { font-family: monospace; font-size: 1.1rem; font-weight: 700; color: var(--vox-orange, #ff8c42); min-width: 2rem; text-align: center; }
    .track-info { flex: 1; }
    .track-name { font-weight: 600; font-size: 0.9rem; }
    .track-artist { color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 0.2rem; }
    .popularity-bar { display: flex; align-items: center; gap: 0.75rem; min-width: 140px; }
    .bar-fill { height: 4px; background: var(--vox-orange, #ff8c42); border-radius: 2px; transition: width 0.4s; }
    .bar-label { font-size: 0.75rem; color: rgba(255,255,255,0.5); min-width: 2rem; text-align: right; }
    .skeleton-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .skeleton-row { background: var(--vox-surface); border-radius: 0.75rem; height: 70px; animation: pulse 1.5s ease-in-out infinite; }
    .empty-state, .error-state { padding: 2rem; text-align: center; color: rgba(255,255,255,0.5); }
    .error-state { color: rgba(239,68,68,0.9); }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  `],
})
export class TrendingComponent implements OnInit {
  isLoading  = signal(true);
  hasError   = signal(false);
  tracks     = signal<TopTrack[]>([]);
  skeletonRows = Array(10).fill(0);

  constructor(private stats: StatsService) {}

  ngOnInit() {
    this.stats.getTopTracks(25).subscribe({
      next: d => { this.tracks.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }
}
