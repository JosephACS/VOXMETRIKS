import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StatsService } from '../../analytics/services/stats.service';
import { LoadRecord } from '../../../shared/models/api.models';

@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page-header">
      <h1>Data Explorer</h1>
      <p class="page-subtitle">Historial de cargas del Data Warehouse</p>
    </div>

    <div *ngIf="isLoading()" class="skeleton-list">
      <div *ngFor="let s of skeletonRows" class="skeleton-row"></div>
    </div>

    <div *ngIf="!isLoading() && loads().length">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Fecha</th>
            <th>Modo</th>
            <th>Registros Nuevos</th>
            <th>Total Raw</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let l of loads()">
            <td class="mono">{{ l.id_carga ?? '—' }}</td>
            <td>{{ l.fecha_carga ? (l.fecha_carga | date:'dd/MM/yyyy HH:mm') : '—' }}</td>
            <td><span class="badge">{{ l.modo ?? '—' }}</span></td>
            <td class="mono">{{ l.registros_nuevos ?? '—' }}</td>
            <td class="mono">{{ l.total_raw ?? '—' }}</td>
            <td>
              <span class="status-badge" [class.status-ok]="l.estado === 'ok'" [class.status-err]="l.estado !== 'ok'">
                {{ l.estado ?? '—' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div *ngIf="!isLoading() && !loads().length && !hasError()" class="empty-state">
      <p>No hay registros de carga disponibles.</p>
    </div>

    <div *ngIf="hasError()" class="error-state">
      <p>⚠️ Error al cargar historial. Verifica que FastAPI esté corriendo.</p>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .page-subtitle { color: rgba(255,255,255,0.5); margin-top: 0.25rem; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .data-table th { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--vox-border); color: rgba(255,255,255,0.5); font-size: 0.75rem; text-transform: uppercase; }
    .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .mono { font-family: monospace; }
    .badge { background: rgba(255,255,255,0.1); padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; }
    .status-badge { padding: 0.2rem 0.6rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600; }
    .status-ok { background: rgba(16,185,129,0.15); color: #10b981; }
    .status-err { background: rgba(239,68,68,0.15); color: #ef4444; }
    .skeleton-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .skeleton-row { background: var(--vox-surface); border-radius: 0.5rem; height: 48px; animation: pulse 1.5s ease-in-out infinite; }
    .empty-state, .error-state { padding: 2rem; text-align: center; color: rgba(255,255,255,0.4); }
    .error-state { color: rgba(239,68,68,0.9); }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  `],
})
export class ExplorerComponent implements OnInit {
  isLoading  = signal(true);
  hasError   = signal(false);
  loads      = signal<LoadRecord[]>([]);
  skeletonRows = Array(8).fill(0);

  constructor(private stats: StatsService) {}

  ngOnInit() {
    this.stats.getLastLoads(50).subscribe({
      next: d => { this.loads.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }
}
