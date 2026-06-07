import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import {
  UiPreferencesService,
  AppTheme,
  AppLanguage,
  DefaultRecords,
  LoadMode,
} from '../../../core/services/ui-preferences.service';
import { TranslationKey } from '../../../core/i18n/translations';
import { StatsService } from '../../analytics/services/stats.service';
import { HealthResponse } from '../../../shared/models/api.models';

type SettingsTab = 'general' | 'api' | 'warehouse' | 'pipeline';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
})
export class SettingsComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  private auth = inject(AuthService);
  private i18n = inject(I18nService);
  private stats = inject(StatsService);
  ui = inject(UiPreferencesService);

  activeTab = signal<SettingsTab>('general');
  healthLoading = signal(false);
  healthError = signal(false);
  health = signal<HealthResponse | null>(null);

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

  themeOptions = computed(() => {
    this.i18n.tick();
    return [
      { value: 'dark' as AppTheme, label: this.i18n.t('settings.theme.dark') },
      { value: 'light' as AppTheme, label: this.i18n.t('settings.theme.light') },
      { value: 'system' as AppTheme, label: this.i18n.t('settings.theme.system') },
    ];
  });

  languageOptions = computed(() => {
    this.i18n.tick();
    return [
      { value: 'es' as AppLanguage, label: this.i18n.t('settings.lang.es') },
      { value: 'en' as AppLanguage, label: this.i18n.t('settings.lang.en') },
    ];
  });

  recordOptions = computed(() => {
    this.i18n.tick();
    return [
      { value: '100k' as DefaultRecords, label: this.i18n.t('settings.pipeline.records100k') },
      { value: '200k' as DefaultRecords, label: this.i18n.t('settings.pipeline.records200k') },
      { value: '300k' as DefaultRecords, label: this.i18n.t('settings.pipeline.records300k') },
    ];
  });

  loadModeOptions = computed(() => {
    this.i18n.tick();
    return [
      { value: 'incremental' as LoadMode, label: this.i18n.t('settings.pipeline.incremental') },
      { value: 'full' as LoadMode, label: this.i18n.t('settings.pipeline.full') },
    ];
  });

  activeThemeLabel = computed(() => {
    this.i18n.tick();
    return this.ui.resolvedTheme() === 'dark'
      ? this.i18n.t('settings.theme.activeDark')
      : this.i18n.t('settings.theme.activeLight');
  });

  private readonly allTabs: { id: SettingsTab; labelKey: TranslationKey; iconKey: string }[] = [
    { id: 'general', labelKey: 'settings.tab.general', iconKey: 'settings' },
    { id: 'api', labelKey: 'settings.tab.api', iconKey: 'link' },
    { id: 'warehouse', labelKey: 'settings.tab.warehouse', iconKey: 'database' },
    { id: 'pipeline', labelKey: 'settings.tab.pipeline', iconKey: 'zap' },
  ];

  tabs = computed(() => {
    this.i18n.tick();
    const list = this.auth.hasEngineerAccess()
      ? this.allTabs
      : this.allTabs.filter((t) => t.id !== 'pipeline');
    return list.map((t) => ({ ...t, label: this.i18n.t(t.labelKey) }));
  });

  ngOnInit() {
    this.refreshHealth();
  }

  selectTab(tab: SettingsTab) {
    this.activeTab.set(tab);
    if (tab === 'api') this.refreshHealth();
  }

  refreshHealth() {
    this.healthLoading.set(true);
    this.healthError.set(false);
    this.stats.getHealth().subscribe({
      next: (h) => {
        this.health.set(h);
        this.healthLoading.set(false);
      },
      error: () => {
        this.healthError.set(true);
        this.healthLoading.set(false);
      },
    });
  }

  healthStatusClass(): string {
    if (this.healthError() || this.healthLoading()) return 'status-warn';
    const s = this.health()?.status;
    if (s === 'ok') return 'status-ok';
    if (s === 'degraded') return 'status-warn';
    return 'status-error';
  }

  healthStatusText(): string {
    if (this.healthLoading()) return 'Comprobando estado del sistema…';
    if (this.healthError()) return 'No se pudo contactar el backend en /health';
    const h = this.health();
    if (!h) return 'Estado desconocido';
    if (h.status === 'ok') return `Sistema operativo · ${h.tables.length} tablas en warehouse`;
    if (h.status === 'degraded') return 'Sistema degradado · base de datos no encontrada';
    return `Estado: ${h.status}`;
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
