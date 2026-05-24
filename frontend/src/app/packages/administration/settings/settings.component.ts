import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';

type SettingsTab = 'general' | 'api' | 'warehouse' | 'pipeline';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
})
export class SettingsComponent {
  private iconRender = inject(IconRenderService);

  activeTab = signal<SettingsTab>('general');

  theme = signal('dark');
  language = signal('es');
  compactMode = signal(false);
  showKpis = signal(true);

  defaultRecords = signal<'100k' | '200k' | '300k'>('100k');
  loadMode = signal('incremental');
  autoRefresh = signal(false);

  apiUrl = environment.apiUrl;
  warehousePath = 'data/warehouse/voxmetrik.duckdb';

  goldTables = [
    'dim_usuario', 'dim_artista', 'dim_genero', 'dim_album',
    'dim_track', 'dim_playlist', 'dim_tiempo', 'fact_streaming',
  ];

  aggregations = [
    'agg_top_artistas', 'agg_genero_popularidad',
    'agg_distribucion_energia', 'agg_tracks_populares',
  ];

  tabs: { id: SettingsTab; label: string; iconKey: string }[] = [
    { id: 'general', label: 'General', iconKey: 'settings' },
    { id: 'api', label: 'API', iconKey: 'link' },
    { id: 'warehouse', label: 'Warehouse', iconKey: 'database' },
    { id: 'pipeline', label: 'Pipeline ELT', iconKey: 'zap' },
  ];

  recordOptions = [
    { value: '100k' as const, label: '100.000 registros' },
    { value: '200k' as const, label: '200.000 registros' },
    { value: '300k' as const, label: '300.000 registros' },
  ];

  selectTab(tab: SettingsTab) {
    this.activeTab.set(tab);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
