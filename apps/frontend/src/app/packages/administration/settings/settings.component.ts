import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, computed, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
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
import { UserService } from '../../users/services/user.service';
import { HealthResponse, UserPreferencesUpdate } from '../../../shared/models/api.models';

type SettingsTab = 'general' | 'api' | 'warehouse' | 'pipeline';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe, RouterModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
})
export class SettingsComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);
  private auth = inject(AuthService);
  private i18n = inject(I18nService);
  private stats = inject(StatsService);
  private userSvc = inject(UserService);
  ui = inject(UiPreferencesService);

  activeTab = signal<SettingsTab>('general');
  healthLoading = signal(false);
  healthError = signal(false);
  health = signal<HealthResponse | null>(null);
  prefsSaving = signal(false);
  prefsFeedback = signal<'ok' | 'error' | null>(null);

  recommendationsEnabled = signal(true);
  privacyPublic = signal(false);
  audioQuality = signal('high');
  favoriteGenre = signal('');

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

  audioQualityOptions = computed(() => {
    this.i18n.tick();
    return [
      { value: 'high', label: this.i18n.t('settings.audio.high') },
      { value: 'normal', label: this.i18n.t('settings.audio.normal') },
      { value: 'low', label: this.i18n.t('settings.audio.low') },
    ];
  });

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

  currentUser = computed(() => this.auth.state().user);

  roleLabel = computed(() => {
    this.i18n.tick();
    const role = (this.currentUser()?.role ?? 'user').toLowerCase();
    if (role === 'admin') return this.i18n.t('shell.role.admin');
    if (role === 'engineer') return this.i18n.t('shell.role.engineer');
    return this.i18n.t('shell.role.user');
  });

  accessScopeLabel = computed(() => {
    this.i18n.tick();
    return this.auth.hasEngineerAccess()
      ? this.i18n.t('settings.scope.engineer')
      : this.i18n.t('settings.scope.user');
  });

  healthVisibilityNote = computed(() => {
    this.i18n.tick();
    const h = this.health();
    if (!h || this.healthError()) return '';
    return h.database || h.tables?.length
      ? this.i18n.t('settings.health.verbose')
      : this.i18n.t('settings.health.public');
  });

  private readonly engineerTabs: SettingsTab[] = ['warehouse', 'pipeline'];

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
      : this.allTabs.filter((t) => !this.engineerTabs.includes(t.id));
    return list.map((t) => ({ ...t, label: this.i18n.t(t.labelKey) }));
  });

  ngOnInit() {
    this.refreshHealth();
    this.loadBusinessPreferences();
  }

  selectTab(tab: SettingsTab) {
    this.activeTab.set(tab);
    if (tab === 'api') this.refreshHealth();
  }

  onThemeChange(theme: AppTheme) {
    this.ui.setTheme(theme);
    this.patchBusinessPreferences({ dark_mode: this.ui.isVisuallyDark(theme) });
  }

  toggleRecommendations(enabled: boolean) {
    this.recommendationsEnabled.set(enabled);
    this.patchBusinessPreferences({ recommendations_enabled: enabled });
  }

  togglePrivacyPublic(enabled: boolean) {
    this.privacyPublic.set(enabled);
    this.patchBusinessPreferences({ privacy_public: enabled });
  }

  onAudioQualityChange(value: string) {
    this.audioQuality.set(value);
    this.patchBusinessPreferences({ audio_quality: value });
  }

  onFavoriteGenreBlur() {
    const genre = this.favoriteGenre().trim();
    this.patchBusinessPreferences({ favorite_genre: genre || undefined });
  }

  private loadBusinessPreferences() {
    this.userSvc.getMe().subscribe({
      next: (p) => {
        const prefs = p.preferences;
        if (prefs?.dark_mode != null) {
          this.ui.syncThemeFromDarkMode(prefs.dark_mode);
        }
        this.recommendationsEnabled.set(prefs?.recommendations_enabled ?? true);
        this.privacyPublic.set(prefs?.privacy_public ?? false);
        this.audioQuality.set(prefs?.audio_quality ?? 'high');
        this.favoriteGenre.set(p.favorite_genre ?? '');
      },
    });
  }

  private patchBusinessPreferences(body: UserPreferencesUpdate) {
    this.prefsSaving.set(true);
    this.prefsFeedback.set(null);
    this.userSvc.updatePreferences(body).subscribe({
      next: (u) => {
        this.prefsSaving.set(false);
        this.prefsFeedback.set('ok');
        if (u.preferences?.dark_mode != null) {
          this.ui.syncThemeFromDarkMode(u.preferences.dark_mode);
        }
        if (body.favorite_genre !== undefined) {
          this.favoriteGenre.set(u.favorite_genre ?? '');
        }
        setTimeout(() => this.prefsFeedback.set(null), 2500);
      },
      error: () => {
        this.prefsSaving.set(false);
        this.prefsFeedback.set('error');
      },
    });
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
    this.i18n.tick();
    if (this.healthLoading()) return this.i18n.t('settings.health.checking');
    if (this.healthError()) return this.i18n.t('settings.health.unreachable');
    const h = this.health();
    if (!h) return this.i18n.t('settings.health.unknown');
    if (h.status === 'ok') return this.i18n.t('settings.health.ok', { count: h.table_count });
    if (h.status === 'degraded') return this.i18n.t('settings.health.degraded');
    return this.i18n.t('settings.health.status', { status: h.status });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
