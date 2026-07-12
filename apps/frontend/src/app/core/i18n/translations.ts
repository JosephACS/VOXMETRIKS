import { AppLanguage } from '../services/ui-preferences.service';
import { LOCALE_ES as ES_CORE } from './locales/es';
import { ENTERPRISE_ES } from './locales/enterprise.es';

export const LOCALE_ES = { ...ES_CORE, ...ENTERPRISE_ES } as const;

export type TranslationKey = keyof typeof LOCALE_ES | string;

/** Spanish bundle (default, eager). English loads on demand. */
export const TRANSLATIONS = {
  es: LOCALE_ES,
} as const;

export type LazyLocale = Exclude<AppLanguage, 'es'>;

export async function loadLocale(lang: LazyLocale): Promise<Record<string, string>> {
  if (lang === 'en') {
    const [mod, ent] = await Promise.all([
      import('./locales/en'),
      import('./locales/enterprise.en'),
    ]);
    return { ...mod.LOCALE_EN, ...ent.ENTERPRISE_EN } as Record<string, string>;
  }
  return LOCALE_ES as Record<string, string>;
}
