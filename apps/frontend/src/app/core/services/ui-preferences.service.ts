import { Injectable, signal, computed } from '@angular/core';

export type AppTheme = 'dark' | 'light' | 'system';
export type AppLanguage = 'es' | 'en';
export type DefaultRecords = '100k' | '200k' | '300k';
export type LoadMode = 'incremental' | 'full';

export interface UiPreferences {
  theme: AppTheme;
  language: AppLanguage;
  compactMode: boolean;
  showKpis: boolean;
  defaultRecords: DefaultRecords;
  loadMode: LoadMode;
  autoRefresh: boolean;
}

const STORAGE_KEY = 'voxmetrik_ui_prefs';

const DEFAULTS: UiPreferences = {
  theme: 'system',
  language: 'es',
  compactMode: false,
  showKpis: true,
  defaultRecords: '100k',
  loadMode: 'incremental',
  autoRefresh: false,
};

@Injectable({ providedIn: 'root' })
export class UiPreferencesService {
  private readonly prefs = signal<UiPreferences>(this.load());

  readonly theme = computed(() => this.prefs().theme);
  readonly language = computed(() => this.prefs().language);
  readonly compactMode = computed(() => this.prefs().compactMode);
  readonly showKpis = computed(() => this.prefs().showKpis);
  readonly defaultRecords = computed(() => this.prefs().defaultRecords);
  readonly loadMode = computed(() => this.prefs().loadMode);
  readonly autoRefresh = computed(() => this.prefs().autoRefresh);
  readonly resolvedTheme = computed(() => this.resolveTheme(this.prefs().theme));

  private mediaQuery: MediaQueryList | null = null;
  private mediaHandler = () => {
    if (this.prefs().theme === 'system') this.applyTheme();
  };

  constructor() {
    this.applyAll();
    if (typeof window !== 'undefined') {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      this.mediaQuery.addEventListener('change', this.mediaHandler);
    }
  }

  setTheme(theme: AppTheme): void {
    this.patch({ theme });
  }

  /** Flip between explicit dark/light for the topbar toggle (persists preference). */
  toggleDarkLight(): void {
    const next = this.isVisuallyDark() ? 'light' : 'dark';
    this.setTheme(next);
  }

  /** Maps API dark_mode flag to local theme (dark / light). */
  syncThemeFromDarkMode(darkMode: boolean): void {
    this.patch({ theme: darkMode ? 'dark' : 'light' });
  }

  /** Resolves whether the active theme is visually dark (for API dark_mode sync). */
  isVisuallyDark(theme: AppTheme = this.prefs().theme): boolean {
    return this.resolveTheme(theme) === 'dark';
  }

  setLanguage(language: AppLanguage): void {
    this.patch({ language });
  }

  setCompactMode(compactMode: boolean): void {
    this.patch({ compactMode });
  }

  setShowKpis(showKpis: boolean): void {
    this.patch({ showKpis });
  }

  setDefaultRecords(defaultRecords: DefaultRecords): void {
    this.patch({ defaultRecords });
  }

  setLoadMode(loadMode: LoadMode): void {
    this.patch({ loadMode });
  }

  setAutoRefresh(autoRefresh: boolean): void {
    this.patch({ autoRefresh });
  }

  private patch(partial: Partial<UiPreferences>): void {
    const next = { ...this.prefs(), ...partial };
    this.prefs.set(next);
    this.persist(next);
    this.applyAll();
  }

  private applyAll(): void {
    this.applyTheme();
    this.applyCompact();
    this.applyLanguage();
  }

  private applyTheme(): void {
    if (typeof document === 'undefined') return;
    const resolved = this.resolveTheme(this.prefs().theme);
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.style.colorScheme = resolved;
    const meta = document.querySelector('meta[name="theme-color"]');
    meta?.setAttribute('content', resolved === 'dark' ? '#0C1110' : '#F3F6F4');
  }

  private applyCompact(): void {
    if (typeof document === 'undefined') return;
    document.documentElement.toggleAttribute('data-compact', this.prefs().compactMode);
  }

  private applyLanguage(): void {
    if (typeof document === 'undefined') return;
    document.documentElement.lang = this.prefs().language;
  }

  private resolveTheme(theme: AppTheme): 'dark' | 'light' {
    if (theme !== 'system') return theme;
    if (typeof window === 'undefined') return 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  private load(): UiPreferences {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { ...DEFAULTS };
      const parsed = { ...DEFAULTS, ...JSON.parse(raw) } as UiPreferences;
      if (parsed.theme !== 'dark' && parsed.theme !== 'light' && parsed.theme !== 'system') {
        parsed.theme = 'system';
      }
      return parsed;
    } catch {
      return { ...DEFAULTS };
    }
  }

  private persist(prefs: UiPreferences): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch {
      /* ignore quota errors */
    }
  }
}
