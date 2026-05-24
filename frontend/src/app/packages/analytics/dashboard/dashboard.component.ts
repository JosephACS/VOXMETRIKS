import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../services/stats.service';
import { StatsSummary, TopTrack, LoadRecord } from '../../../shared/models/api.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Dashboard</h1>
      <p class="page-subtitle">Resumen general de VOXMETRIK</p>
    </div>

    <div *ngIf="isLoading()" class="skeleton-grid">
      <div *ngFor="let s of skeletonCards" class="skeleton-card"></div>
    </div>

    <div *ngIf="!isLoading() && summary()" class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Tracks</div>
        <div class="kpi-value">{{ fmt(summary()!.total_tracks) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Artistas</div>
        <div class="kpi-value">{{ fmt(summary()!.total_artistas) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Géneros</div>
        <div class="kpi-value">{{ fmt(summary()!.total_generos) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Álbumes</div>
        <div class="kpi-value">{{ fmt(summary()!.total_albumes) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Popularidad Prom.</div>
        <div class="kpi-value">{{ (summary()!.promedio_popularidad ?? 0) | number:'1.1-1' }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Energy Prom.</div>
        <div class="kpi-value">{{ (summary()!.promedio_energy ?? 0) | number:'1.2-2' }}</div>
      </div>
    </div>

    <div *ngIf="!isLoading() && topTracks().length" class="section">
      <h2 class="section-title">Top Tracks</h2>
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Track</th>
            <th>Artista</th>
            <th>Popularidad</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let t of topTracks(); let i = index">
            <td class="mono">{{ i + 1 }}</td>
            <td>{{ t.nombre_track ?? '—' }}</td>
            <td>{{ t.nombre_artista ?? '—' }}</td>
            <td>{{ t.popularity ?? '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div *ngIf="hasError()" class="error-state">
      <p>⚠️ No se pudo conectar con el backend. Verifica que FastAPI esté corriendo en <code>http://localhost:8000</code></p>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .page-subtitle { color: rgba(255,255,255,0.5); margin-top: 0.25rem; }
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .kpi-card { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1.25rem 1.5rem; }
    .kpi-label { font-size: 0.75rem; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }
    .kpi-value { font-size: 1.75rem; font-weight: 700; color: var(--vox-orange, #ff8c42); font-variant-numeric: tabular-nums; }
    .skeleton-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .skeleton-card { background: var(--vox-surface); border-radius: 0.75rem; height: 100px; animation: pulse 1.5s ease-in-out infinite; }
    .section { margin-top: 2rem; }
    .section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: rgba(255,255,255,0.8); }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .data-table th { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--vox-border); color: rgba(255,255,255,0.5); font-weight: 500; font-size: 0.75rem; text-transform: uppercase; }
    .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .mono { font-family: monospace; color: rgba(255,255,255,0.4); }
    .error-state { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 0.75rem; padding: 1.5rem; color: rgba(239,68,68,0.9); }
    .error-state code { background: rgba(0,0,0,0.3); padding: 0.1rem 0.4rem; border-radius: 0.25rem; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  `],
})
export class DashboardComponent implements OnInit {
  isLoading  = signal(true);
  hasError   = signal(false);
  summary    = signal<StatsSummary | null>(null);
  topTracks  = signal<TopTrack[]>([]);
  loads      = signal<LoadRecord[]>([]);
  skeletonCards = Array(6).fill(0);

  constructor(private stats: StatsService) {}

  ngOnInit() {
    let done = 0;
    const finish = () => { if (++done >= 2) this.isLoading.set(false); };

    this.stats.getSummary().subscribe({
      next: d => { this.summary.set(d); finish(); },
      error: () => { this.hasError.set(true); finish(); },
    });

    this.stats.getTopTracks(10).subscribe({
      next: d => { this.topTracks.set(d ?? []); finish(); },
      error: () => finish(),
    });
  }

  fmt(val?: number): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000)     return `${(val / 1_000).toFixed(1)}K`;
    return val.toString();
  }
}
