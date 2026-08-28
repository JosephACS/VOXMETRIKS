import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, computed, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';
import { I18nService } from '../../../core/services/i18n.service';
import { NotificationService } from '../../../core/services/notification.service';
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
import {
  SecurityApiService,
  TrustedDevice,
} from '../../personal-account/services/security-api.service';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';
import { SpotifyIntegrationService } from '../../../core/integrations/spotify/spotify-integration.service';

type SettingsTab = 'profile' | 'preferences' | 'connections' | 'security' | 'api' | 'warehouse' | 'pipeline';

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
  private securityApi = inject(SecurityApiService);
  private notifications = inject(NotificationService);
  private confirmDlg = inject(ConfirmDialogService);
  readonly spotify = inject(SpotifyIntegrationService);
  ui = inject(UiPreferencesService);

  activeTab = signal<SettingsTab>('profile');
  healthLoading = signal(false);
  healthError = signal(false);
  health = signal<HealthResponse | null>(null);
  prefsSaving = signal(false);
  prefsFeedback = signal<'ok' | 'error' | null>(null);

  recommendationsEnabled = signal(true);
  privacyPublic = signal(false);
  audioQuality = signal('high');
  favoriteGenre = signal('');
  spotifyBusy = signal(false);

  passwordCurrent = signal('');
  passwordNew = signal('');
  passwordConfirm = signal('');
  passwordRevokeOthers = signal(true);
  passwordSaving = signal(false);

  devices = signal<TrustedDevice[]>([]);
  devicesLoading = signal(false);
  devicesBusy = signal(false);
  sessionsBusy = signal(false);

  apiUrl = environment.apiUrl;
  /** Engineer-only warehouse path hint (not shown to normal users). */
  warehousePath = 'data/warehouse/voxmetrik.duckdb';

  goldTables = [
    'dim_usuario',
    'dim_artista',
    'dim_genero',
    'dim_album',
    'dim_track',
    'dim_playlist',
    'dim_tiempo',
    'fact_streaming',
  ];

  aggregations = [
    'agg_top_artistas',
    'agg_genero_popularidad',
    'agg_distribucion_energia',
    'agg_tracks_populares',
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

  userInitial = computed(() => {
    const value = this.currentUser()?.username?.trim() || this.currentUser()?.email?.trim() || 'U';
    return value.charAt(0).toUpperCase();
  });

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

  private readonly technicalTabIds: SettingsTab[] = ['api', 'warehouse', 'pipeline'];
  technicalToolsExpanded = signal(false);

  private readonly allTabs: { id: SettingsTab; labelKey: TranslationKey; iconKey: string }[] = [
    { id: 'profile', labelKey: 'settings.tab.profile', iconKey: 'user' },
    { id: 'preferences', labelKey: 'settings.tab.preferences', iconKey: 'settings' },
    { id: 'connections', labelKey: 'settings.tab.connections', iconKey: 'link' },
    { id: 'security', labelKey: 'settings.tab.security', iconKey: 'lock' },
    { id: 'api', labelKey: 'settings.tab.api', iconKey: 'link' },
    { id: 'warehouse', labelKey: 'settings.tab.warehouse', iconKey: 'database' },
    { id: 'pipeline', labelKey: 'settings.tab.pipeline', iconKey: 'zap' },
  ];

  hasTechnicalAccess = computed(() => this.auth.hasEngineerAccess());

  userTabs = computed(() => {
    this.i18n.tick();
    return this.allTabs
      .filter((t) => !this.technicalTabIds.includes(t.id))
      .map((t) => ({ ...t, label: this.i18n.t(t.labelKey) }));
  });

  technicalTabs = computed(() => {
    this.i18n.tick();
    if (!this.auth.hasEngineerAccess()) return [];
    return this.allTabs
      .filter((t) => this.technicalTabIds.includes(t.id))
      .map((t) => ({ ...t, label: this.i18n.t(t.labelKey) }));
  });

  /** @deprecated kept for any residual references */
  tabs = computed(() => [...this.userTabs(), ...this.technicalTabs()]);

  toggleTechnicalTools(): void {
    this.technicalToolsExpanded.update((v) => !v);
  }

  ngOnInit() {
    this.loadBusinessPreferences();
    const settingsQuery = new URLSearchParams(window.location.search);
    if (settingsQuery.get('tab') === 'connections') {
      this.activeTab.set('connections');
    }
    void this.spotify.initializeFromCurrentUrl();
  }

  selectTab(tab: SettingsTab) {
    this.activeTab.set(tab);
    if (this.technicalTabIds.includes(tab)) this.technicalToolsExpanded.set(true);
    if (tab === 'api') this.refreshHealth();
    if (tab === 'security') this.loadDevices();
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

  async connectSpotify(): Promise<void> {
    if (this.spotifyBusy()) return;
    this.spotifyBusy.set(true);
    try {
      await this.spotify.connect();
    } catch (error) {
      this.spotifyBusy.set(false);
      this.notifications.error('No pudimos conectar Spotify', error instanceof Error ? error.message : 'Revisa la configuración.');
    }
  }

  disconnectSpotify(): void {
    this.spotify.disconnect();
    this.notifications.success('Spotify desconectado', 'Voxmetriks seguirá funcionando con sus datos y funciones internas.');
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
    if (this.prefsSaving()) return;
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
        this.notifications.success(
          this.i18n.t('settings.business.saved'),
          this.i18n.t('settings.feedback.savedBody'),
        );
        setTimeout(() => this.prefsFeedback.set(null), 2500);
      },
      error: () => {
        this.prefsSaving.set(false);
        this.prefsFeedback.set('error');
        this.notifications.error(
          this.i18n.t('settings.business.error'),
          this.i18n.t('settings.feedback.errorBody'),
        );
      },
    });
  }

  loadDevices(): void {
    this.devicesLoading.set(true);
    this.securityApi.listDevices().subscribe({
      next: (res) => {
        this.devices.set(res.items ?? []);
        this.devicesLoading.set(false);
      },
      error: () => {
        this.devices.set([]);
        this.devicesLoading.set(false);
      },
    });
  }

  submitPasswordChange(): void {
    if (this.passwordSaving()) return;
    const current = this.passwordCurrent().trim();
    const next = this.passwordNew().trim();
    const confirm = this.passwordConfirm().trim();
    if (!current || !next || !confirm) {
      this.notifications.error(
        this.i18n.t('settings.security.passwordTitle'),
        this.i18n.t('settings.security.passwordIncomplete'),
      );
      return;
    }
    if (next !== confirm) {
      this.notifications.error(
        this.i18n.t('settings.security.passwordTitle'),
        this.i18n.t('settings.security.passwordMismatch'),
      );
      return;
    }
    this.passwordSaving.set(true);
    this.securityApi
      .changePassword({
        current_password: current,
        new_password: next,
        confirm_password: confirm,
        revoke_other_sessions: this.passwordRevokeOthers(),
      })
      .subscribe({
        next: () => {
          this.passwordSaving.set(false);
          this.passwordCurrent.set('');
          this.passwordNew.set('');
          this.passwordConfirm.set('');
          this.notifications.success(
            this.i18n.t('settings.security.passwordUpdated'),
            this.i18n.t('settings.feedback.savedBody'),
          );
        },
        error: (err) => {
          this.passwordSaving.set(false);
          this.notifications.error(
            this.i18n.t('settings.security.passwordTitle'),
            SecurityApiService.errorMessage(err) || this.i18n.t('settings.feedback.errorBody'),
          );
        },
      });
  }

  async revokeDevice(deviceId: number): Promise<void> {
    if (this.devicesBusy()) return;
    const ok = await this.confirmDlg.open({
      title: this.i18n.t('settings.security.revokeDevice'),
      message: this.i18n.t('settings.security.revokeDeviceConfirm'),
      confirmLabel: this.i18n.t('settings.security.revokeDevice'),
      danger: true,
    });
    if (!ok) return;
    this.devicesBusy.set(true);
    this.securityApi.revokeDevice(deviceId).subscribe({
      next: () => {
        this.devicesBusy.set(false);
        this.notifications.success(this.i18n.t('settings.security.deviceRevoked'));
        this.loadDevices();
      },
      error: (err) => {
        this.devicesBusy.set(false);
        this.notifications.error(
          this.i18n.t('settings.security.revokeDevice'),
          SecurityApiService.errorMessage(err) || this.i18n.t('settings.feedback.errorBody'),
        );
      },
    });
  }

  async revokeOtherSessions(): Promise<void> {
    if (this.sessionsBusy()) return;
    const ok = await this.confirmDlg.open({
      title: this.i18n.t('settings.security.revokeOtherSessions'),
      message: this.i18n.t('settings.security.revokeSessionsConfirm'),
      confirmLabel: this.i18n.t('settings.security.revokeOtherSessions'),
      danger: true,
    });
    if (!ok) return;
    this.sessionsBusy.set(true);
    this.securityApi.revokeOtherSessions().subscribe({
      next: () => {
        this.sessionsBusy.set(false);
        this.notifications.success(this.i18n.t('settings.security.sessionsRevoked'));
      },
      error: (err) => {
        this.sessionsBusy.set(false);
        this.notifications.error(
          this.i18n.t('settings.security.revokeOtherSessions'),
          SecurityApiService.errorMessage(err) || this.i18n.t('settings.feedback.errorBody'),
        );
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
