import { Injectable, inject, computed } from '@angular/core';
import { TRANSLATIONS, TranslationKey } from '../i18n/translations';
import { UiPreferencesService } from './ui-preferences.service';

type Params = Record<string, string | number>;

@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly ui = inject(UiPreferencesService);

  /** Fuerza recálculo en plantillas al cambiar idioma. */
  readonly tick = computed(() => this.ui.language());

  t(key: TranslationKey | string, params?: Params): string {
    const lang = this.ui.language();
    const dict = TRANSLATIONS[lang] as Record<string, string>;
    const fallback = TRANSLATIONS.es as Record<string, string>;
    let text = dict[key] ?? fallback[key] ?? key;

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
