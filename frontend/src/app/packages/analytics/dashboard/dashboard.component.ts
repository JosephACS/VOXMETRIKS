import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../services/stats.service';
import { StatsSummary, TopTrack } from '../../../shared/models/api.models';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, KpiCardComponent],
  template: `
    <header class="vx-page-header">
      <div>
        <h1>Dashboard</h1>
        <p class="page-subtitle">Resumen del catálogo musical</p>
      </div>
      <span class="vx-badge live-badge">
        <span [innerHTML]="icon('activity', 12)"></span> En vivo
      </span>
    </header>

    @if (isLoading()) {
      <div class="skeleton-grid">
        @for (s of skeletonCards; track s) {
          <div class="skeleton-card"></div>
        }
      </div>
    }

    @if (!isLoading() && summary()) {
      <section class="vx-kpi-grid">
        <app-kpi-card label="Tracks" [value]="summary()!.total_tracks" iconKey="music" color="primary" subtitle="en catálogo" />
        <app-kpi-card label="Artistas" [value]="summary()!.total_artistas" iconKey="users" color="info" subtitle="únicos" />
        <app-kpi-card label="Géneros" [value]="summary()!.total_generos" iconKey="layers" color="warning" subtitle="clasificados" />
        <app-kpi-card label="Álbumes" [value]="summary()!.total_albumes" iconKey="album" color="secondary" subtitle="registrados" />
        <app-kpi-card label="Popularidad" [value]="popularityKpi()" iconKey="star" color="primary" subtitle="promedio" />
        <app-kpi-card label="Energía" [value]="energyKpi()" iconKey="zap" color="info" subtitle="promedio" />
      </section>

      <!-- Volumen de datos — conteos reales del warehouse -->
      <section class="glass-panel dataset-strip">
        <div class="dataset-left">
          <span class="dataset-label">Warehouse actual</span>
          <span class="dataset-total">{{ fmt(summary()!.total_tracks) }} <small>tracks en DuckDB</small></span>
        </div>
        <div class="dataset-entities">
          <span class="entity-chip"><strong>{{ fmt(summary()!.total_artistas) }}</strong> artistas</span>
          <span class="entity-chip"><strong>{{ fmt(summary()!.total_generos) }}</strong> géneros</span>
          <span class="entity-chip"><strong>{{ fmt(summary()!.total_albumes) }}</strong> álbumes</span>
          <span class="entity-chip"><strong>{{ fmt(summary()!.total_streams) }}</strong> streams</span>
        </div>
        <span class="dataset-hint">Datos en vivo desde <strong>voxmetrik.duckdb</strong></span>
      </section>

      <section class="glass-panel chart-panel">
        <div class="panel-head">
          <h2>Actividad del catálogo</h2>
          <span class="panel-meta">Últimos 12 meses</span>
        </div>
        <svg viewBox="0 0 480 100" class="vx-mini-chart" aria-hidden="true">
          <defs>
            <linearGradient id="dashArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#ff8c42" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="#ff8c42" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <line x1="0" y1="85" x2="480" y2="85" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
          <polygon [attr.points]="sparkArea()" fill="url(#dashArea)"/>
          <polyline [attr.points]="sparkLine()" fill="none" stroke="#ff8c42" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </section>
    }

    @if (!isLoading() && topTracks().length) {
      <section class="glass-panel table-panel">
        <div class="panel-head">
          <h2>Top Tracks</h2>
          <span class="panel-meta">{{ topTracks().length }} más populares</span>
        </div>
        <div class="table-scroll">
          <table class="vx-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Canción</th>
                <th>Artista</th>
                <th>Popularidad</th>
              </tr>
            </thead>
            <tbody>
              @for (t of topTracks(); track t.nombre_track; let i = $index) {
                <tr>
                  <td class="mono rank">{{ i + 1 }}</td>
                  <td class="track-name">{{ t.nombre_track ?? '—' }}</td>
                  <td>{{ t.nombre_artista ?? '—' }}</td>
                  <td>
                    <div class="pop-cell">
                      <div class="pop-bar"><div class="pop-fill" [style.width.%]="t.popularity ?? 0"></div></div>
                      <span class="mono">{{ t.popularity ?? '—' }}</span>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </section>
    }

    @if (hasError()) {
      <div class="error-state glass-panel">
        <span class="error-icon" [innerHTML]="icon('alert', 20)"></span>
        <p>No se pudo conectar con el backend. Verifica que FastAPI esté corriendo en <code>http://localhost:8000</code></p>
      </div>
    }
  `,
  styles: [`
    .live-badge {
      background: rgba(52,211,153,0.1);
      border-color: rgba(52,211,153,0.25);
      color: #34d399;
    }
    .skeleton-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 0.625rem;
      margin-bottom: var(--section-gap);
    }
    .skeleton-card {
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      height: 88px;
      animation: pulse 1.5s ease-in-out infinite;
    }

    /* Dataset strip */
    .dataset-strip {
      display: flex;
      align-items: center;
      gap: 1.25rem;
      padding: 0.875rem 1.125rem;
      margin-bottom: var(--section-gap);
      flex-wrap: wrap;
    }
    .dataset-left { flex: 1; min-width: 140px; }
    .dataset-label {
      display: block;
      font-size: 0.65rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      margin-bottom: 0.2rem;
    }
    .dataset-total {
      font-family: var(--font-mono);
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text);
    }
    .dataset-total small {
      font-size: 0.75rem;
      font-weight: 400;
      color: var(--text-muted);
    }
    .dataset-entities {
      display: flex;
      flex-wrap: wrap;
      gap: 0.375rem;
    }
    .entity-chip {
      padding: 0.35rem 0.75rem;
      border-radius: 2rem;
      font-size: 0.75rem;
      color: var(--text-muted);
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
    }
    .entity-chip strong {
      color: var(--accent);
      font-family: var(--font-mono);
      font-weight: 700;
    }
    .dataset-hint {
      font-size: 0.75rem;
      color: var(--text-muted);
      white-space: nowrap;
    }
    .dataset-hint strong { color: var(--text); }

    .chart-panel { padding: 0.875rem 1rem; margin-bottom: var(--section-gap); }
    .table-panel { padding: 0; overflow: hidden; margin-bottom: var(--section-gap); }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border-subtle);
    }
    .panel-head h2 { font-size: 0.8125rem; font-weight: 600; margin: 0; color: var(--text); }
    .panel-meta { font-size: 0.65rem; color: var(--text-muted); font-family: var(--font-mono); }
    .table-scroll { overflow-x: auto; }
    .table-panel .vx-table th, .table-panel .vx-table td { padding: 0.5rem 1rem; }
    .mono { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted); }
    .rank { width: 2rem; color: var(--accent); font-weight: 600; }
    .track-name { font-weight: 500; color: var(--text); }
    .pop-cell { display: flex; align-items: center; gap: 0.5rem; min-width: 120px; }
    .pop-bar { flex: 1; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
    .pop-fill { height: 100%; background: linear-gradient(90deg, var(--accent), #148f5e); border-radius: 2px; }
    .error-state {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem 1.125rem;
      color: rgba(239,68,68,0.9);
      border-color: rgba(239,68,68,0.25);
    }
    .error-icon { display: flex; color: #ef4444; flex-shrink: 0; margin-top: 0.1rem; }
    .error-state code {
      background: rgba(0,0,0,0.3);
      padding: 0.1rem 0.4rem;
      border-radius: 0.25rem;
      font-size: 0.75rem;
    }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.45} }

    @media (max-width: 640px) {
      .dataset-hint { width: 100%; }
    }
  `],
})
export class DashboardComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  isLoading = signal(true);
  hasError = signal(false);
  summary = signal<StatsSummary | null>(null);
  topTracks = signal<TopTrack[]>([]);
  skeletonCards = Array(6).fill(0);

  private sparkData = [42, 58, 51, 72, 65, 88, 76, 94, 82, 91, 85, 97];

  constructor(private stats: StatsService) {}

  ngOnInit() {
    let done = 0;
    const finish = () => { if (++done >= 2) this.isLoading.set(false); };

    this.stats.getSummary().subscribe({
      next: (d) => { this.summary.set(d); finish(); },
      error: () => { this.hasError.set(true); finish(); },
    });

    this.stats.getTopTracks(10).subscribe({
      next: (d) => { this.topTracks.set(d ?? []); finish(); },
      error: () => finish(),
    });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  popularityKpi(): number | null {
    const v = this.summary()?.promedio_popularidad;
    return v != null ? Math.round(v * 10) / 10 : null;
  }

  energyKpi(): number | null {
    const v = this.summary()?.promedio_energy;
    return v != null ? Math.round(v * 100) / 100 : null;
  }

  sparkLine(): string {
    return this.sparkData.map((v, i) => `${i * 40},${90 - v * 0.7}`).join(' ');
  }

  sparkArea(): string {
    const line = this.sparkData.map((v, i) => `${i * 40},${90 - v * 0.7}`).join(' ');
    return `0,90 ${line} ${(this.sparkData.length - 1) * 40},90`;
  }

  fmt(val?: number | null): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toLocaleString('es-ES');
  }
}
