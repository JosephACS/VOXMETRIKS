import { AppLanguage } from '../services/ui-preferences.service';
import { LOCALE_ES } from './locales/es';

export type TranslationKey = keyof typeof LOCALE_ES;

/** Spanish bundle (default, eager). English loads on demand. */
export const TRANSLATIONS = {
  es: LOCALE_ES,
} as const;

export type LazyLocale = Exclude<AppLanguage, 'es'>;

export async function loadLocale(lang: LazyLocale): Promise<Record<string, string>> {
  if (lang === 'en') {
    const mod = await import('./locales/en');
    return mod.LOCALE_EN as Record<string, string>;
  }
  return LOCALE_ES as Record<string, string>;
}
