import { Injectable, inject, computed, signal, effect } from '@angular/core';
import { loadLocale, TRANSLATIONS, TranslationKey } from '../i18n/translations';
import { AppLanguage, UiPreferencesService } from './ui-preferences.service';

type Params = Record<string, string | number>;

/**
 * Language priority:
 * 1) Saved UI preference (localStorage via UiPreferencesService)
 * 2) Profile preference when synced into UiPreferencesService
 * 3) Spanish default
 *
 * Missing keys fall back to Spanish, then a safe generic label — never show raw keys.
 */
@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly ui = inject(UiPreferencesService);
  private readonly extraLocales = signal<Partial<Record<AppLanguage, Record<string, string>>>>({});

  readonly tick = computed(() => {
    this.ui.language();
    this.extraLocales();
    return this.ui.language();
  });

  /** Alias for templates: `{{ 'key' | t:lang() }}` */
  readonly lang = this.tick;

  constructor() {
    effect(() => {
      const lang = this.ui.language();
      if (lang === 'es' || this.extraLocales()[lang]) return;
      void this.ensureLocale(lang);
    });
  }

  async ensureLocale(lang: AppLanguage): Promise<void> {
    if (lang === 'es' || this.extraLocales()[lang]) return;
    const dict = await loadLocale(lang);
    this.extraLocales.update((current) => ({ ...current, [lang]: dict }));
  }

  /** Apply profile language only when localStorage has never overridden (still default es and no explicit save is N/A — always prefer stored prefs). */
  applyProfileLanguage(preferred: AppLanguage | string | null | undefined): void {
    if (preferred !== 'es' && preferred !== 'en') return;
    // Priority: existing localStorage language already loaded; only apply profile when storage empty of language override.
    try {
      const raw = localStorage.getItem('voxmetrik_ui_prefs');
      if (raw) {
        const parsed = JSON.parse(raw) as { language?: string };
        if (parsed.language === 'es' || parsed.language === 'en') return;
      }
    } catch {
      /* ignore */
    }
    this.ui.setLanguage(preferred);
  }

  t(key: TranslationKey | string, params?: Params): string {
    const lang = this.ui.language();
    const dict =
      (lang === 'es' ? TRANSLATIONS.es : this.extraLocales()[lang]) ?? TRANSLATIONS.es;
    const fallback = TRANSLATIONS.es as Record<string, string>;
    const missing = fallback['common.missingTranslation'] ?? 'Texto no disponible';
    let text = (dict as Record<string, string>)[key] ?? fallback[key] ?? missing;

    // Never surface dotted i18n keys to users
    if (text === key || (typeof text === 'string' && text.includes('.') && text === String(key))) {
      text = missing;
    }

    if (params) {
      for (const [k, v] of Object.entries(params)) {
        text = text.replace(new RegExp(`\\{\\{${k}\\}\\}`, 'g'), String(v));
      }
    }
    return text;
  }

  greetingKey(): TranslationKey {
    const hour = new Date().getHours();
    if (hour < 12) return 'home.greet.morning';
    if (hour < 19) return 'home.greet.afternoon';
    return 'home.greet.evening';
  }
}
