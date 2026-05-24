/**
 * DashboardComponent
 * ==================
 * Vista principal de analíticas. Carga en paralelo:
 * - Summary (KPI cards)          → GET /api/v1/stats/summary
 * - Top artistas (popularidad)   → GET /api/v1/artists/top
 * - Top tracks                   → GET /api/v1/stats/top-tracks
 * - Distribución energía         → GET /api/v1/stats/energia
 * - Historial de cargas ELT      → GET /api/v1/stats/loads
 *
 * Usa forkJoin para una sola ronda de peticiones HTTP.
 * catchError por endpoint evita que un fallo bloquee los demás.
 */

import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { DecimalPipe, PercentPipe }                     from '@angular/common';
import { RouterLink }                                    from '@angular/router';
import { forkJoin, catchError, of }                      from 'rxjs';

import { StatsService }   from '../../services/stats.service';
import { ArtistsService } from '../../services/artists.service';

import { KpiCardComponent }        from '../../shared/components/kpi-card/kpi-card.component';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';

import {
  StatsSummary,
  TopArtista,
  TopTrack,
  DistribucionEnergia,
  LoadRecord,
} from '../../shared/models/api.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    DecimalPipe,
    PercentPipe,
    RouterLink,
    KpiCardComponent,
    LoadingSpinnerComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl:    './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  private readonly statsService   = inject(StatsService);
  private readonly artistsService = inject(ArtistsService);

  protected readonly isLoading   = signal(true);
  protected readonly hasError    = signal(false);

  protected readonly summary     = signal<StatsSummary | null>(null);
  protected readonly topArtists  = signal<TopArtista[]>([]);
  protected readonly topTracks   = signal<TopTrack[]>([]);
  protected readonly energyDist  = signal<DistribucionEnergia[]>([]);
  protected readonly loadHistory = signal<LoadRecord[]>([]);

  /** Máximo de tracks en la distribución de energía — para normalizar barras */
  protected readonly maxEnergy = computed(() => {
    const arr = this.energyDist();
    if (!arr.length) return 1;
    return Math.max(...arr.map(d => d.cantidad_tracks ?? 0));
  });

  /** Máxima popularidad entre top artistas — para normalizar barras */
  protected readonly maxArtistPop = computed(() => {
    const arr = this.topArtists();
    if (!arr.length) return 1;
    return Math.max(...arr.map(a => a.promedio_popularidad ?? 0));
  });

  ngOnInit(): void {
    forkJoin({
      summary:    this.statsService.getSummary().pipe(catchError(() => of(null))),
      topArtists: this.artistsService.getTopArtists(8).pipe(catchError(() => of([]))),
      topTracks:  this.statsService.getTopTracks(10).pipe(catchError(() => of([]))),
      energyDist: this.statsService.getEnergiaDistribution().pipe(catchError(() => of([]))),
      loads:      this.statsService.getLoadHistory(5).pipe(catchError(() => of([]))),
    }).subscribe({
      next: ({ summary, topArtists, topTracks, energyDist, loads }) => {
        this.summary.set(summary);
        this.topArtists.set(topArtists  as TopArtista[]);
        this.topTracks.set(topTracks    as TopTrack[]);
        this.energyDist.set(energyDist  as DistribucionEnergia[]);
        this.loadHistory.set(loads      as LoadRecord[]);
        this.isLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.isLoading.set(false);
      },
    });
  }

  /** Retorna el ancho de barra como porcentaje del máximo dado */
  protected barWidth(value?: number | null, max?: number | null): string {
    if (!value || !max || max === 0) return '2%';
    return `${Math.max(2, Math.round((value / max) * 100))}%`;
  }

  /** Clase CSS para el badge de estado de carga */
  protected badgeClass(estado: string): string {
    const s = estado?.toLowerCase();
    if (s === 'completado' || s === 'ok' || s === 'success') return 'badge-green';
    if (s === 'error'      || s === 'failed')                return 'badge-red';
    return 'badge-yellow';
  }

  /** Formatea un timestamp ISO a fecha legible en español */
  protected formatDate(iso: string): string {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleDateString('es-EC', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return iso;
    }
  }

  /** Retorna el color de la barra de energía según el rango */
  protected energyColor(rango: string): string {
    const r = rango?.toLowerCase() ?? '';
    if (r.includes('0.8') || r.includes('alto') || r.includes('high')) return 'var(--color-danger)';
    if (r.includes('0.6') || r.includes('medio')) return 'var(--color-warning)';
    if (r.includes('0.4')) return 'var(--color-primary)';
    return 'var(--color-info)';
  }
}
