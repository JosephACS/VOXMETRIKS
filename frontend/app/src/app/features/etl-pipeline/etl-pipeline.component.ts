import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-etl-pipeline',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>ETL Pipeline</h1>
      <p>Data processing and warehouse status</p>
    </div>
    <div class="pipeline-container">
      <div class="pipeline-stage" *ngFor="let stage of stages">
        <div class="stage-icon">{{ stage.icon }}</div>
        <h4>{{ stage.name }}</h4>
        <p class="stage-status" [ngClass]="'status-' + stage.status">{{ stage.status }}</p>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .pipeline-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }
    .pipeline-stage { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 1.5rem; text-align: center; }
    .stage-icon { font-size: 2rem; margin-bottom: 1rem; }
    .pipeline-stage h4 { margin: 0.5rem 0; }
    .stage-status { margin: 0.5rem 0 0 0; font-size: 0.875rem; padding: 0.5rem; border-radius: 0.375rem; }
    .status-active { background: rgba(16,185,129,0.1); color: var(--vox-success); }
    .status-inactive { background: rgba(239,68,68,0.1); color: var(--vox-danger); }
  `]
})
export class EtlPipelineComponent {
  stages = [
    { name: 'Spotify API', icon: '🎵', status: 'active' },
    { name: 'FastAPI ETL', icon: '⚙️', status: 'active' },
    { name: 'DuckDB', icon: '🗄️', status: 'active' },
    { name: 'Analytics', icon: '📊', status: 'active' },
  ];
}
