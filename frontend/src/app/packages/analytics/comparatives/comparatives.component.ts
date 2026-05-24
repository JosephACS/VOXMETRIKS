import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../services/stats.service';
import { GenresService } from '../../streaming/services/genres.service';
import { GeneroPopularidad } from '../../../shared/models/api.models';

@Component({
  selector: 'app-comparatives',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Comparatives</h1>
      <p class="page-subtitle">Comparativa de géneros por popularidad y energía</p>
    </div>

    <div *ngIf="isLoading()" class="skeleton-list">
      <div *ngFor="let s of skeletonRows" class="skeleton-row"></div>
    </div>

    <div *ngIf="!isLoading() && genres().length" class="comparatives-grid">
      <div *ngFor="let g of genres(); let i = index" class="genre-card">
        <div class="genre-name">{{ g.nombre_genero ?? 'Género ' + g.id_genero }}</div>
        <div class="metric-row">
          <span class="metric-label">Popularidad</span>
          <div class="metric-bar">
            <div class="bar-pop" [style.width.%]="g.popularidad_promedio ?? 0"></div>
          </div>
          <span class="metric-val">{{ (g.popularidad_promedio ?? 0) | number:'1.1-1' }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Energía</span>
          <div class="metric-bar">
            <div class="bar-energy" [style.width.%]="(g.energia_promedio ?? 0) * 100"></div>
          </div>
          <span class="metric-val">{{ (g.energia_promedio ?? 0) | number:'1.2-2' }}</span>
        </div>
        <div class="genre-tracks">{{ g.total_tracks ?? 0 }} tracks</div>
      </div>
    </div>

    <div *ngIf="hasError()" class="error-state">
      <p>⚠️ Error al cargar comparativas. Verifica que FastAPI esté corriendo.</p>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .page-subtitle { color: rgba(255,255,255,0.5); margin-top: 0.25rem; }
    .comparatives-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
    .genre-card { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1.25rem; }
    .genre-name { font-weight: 600; margin-bottom: 1rem; }
    .metric-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; font-size: 0.8rem; }
    .metric-label { min-width: 70px; color: rgba(255,255,255,0.5); }
    .metric-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; }
    .bar-pop { height: 100%; background: var(--vox-orange, #ff8c42); border-radius: 3px; }
    .bar-energy { height: 100%; background: var(--vox-purple, #7c3aed); border-radius: 3px; }
    .metric-val { min-width: 36px; text-align: right; color: rgba(255,255,255,0.6); }
    .genre-tracks { font-size: 0.75rem; color: rgba(255,255,255,0.35); margin-top: 0.5rem; }
    .skeleton-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
    .skeleton-row { background: var(--vox-surface); border-radius: 0.75rem; height: 120px; animation: pulse 1.5s ease-in-out infinite; }
    .error-state { padding: 2rem; color: rgba(239,68,68,0.9); }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  `],
})
export class ComparativesComponent implements OnInit {
  isLoading  = signal(true);
  hasError   = signal(false);
  genres     = signal<GeneroPopularidad[]>([]);
  skeletonRows = Array(8).fill(0);

  constructor(private genresSvc: GenresService) {}

  ngOnInit() {
    this.genresSvc.getGenreStats(30).subscribe({
      next: d => { this.genres.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }
}
