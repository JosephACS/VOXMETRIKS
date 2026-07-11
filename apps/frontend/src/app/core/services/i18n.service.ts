import { Injectable, inject, computed, signal, effect } from '@angular/core';
import { loadLocale, TRANSLATIONS, TranslationKey } from '../i18n/translations';
import { AppLanguage, UiPreferencesService } from './ui-preferences.service';

type Params = Record<string, string | number>;

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

  t(key: TranslationKey | string, params?: Params): string {
    const lang = this.ui.language();
    const dict =
      (lang === 'es' ? TRANSLATIONS.es : this.extraLocales()[lang])
      ?? TRANSLATIONS.es;
    const fallback = TRANSLATIONS.es as Record<string, string>;
    let text = (dict as Record<string, string>)[key] ?? fallback[key] ?? key;

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
