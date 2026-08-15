import { AppLanguage } from '../services/ui-preferences.service';
import { LOCALE_ES as ES_CORE } from './locales/es';

/**
 * Eager Spanish core only. Enterprise strings (catalog, billing, artist ops, …)
 * load asynchronously so the initial production bundle stays under budget.
 */
export const TRANSLATIONS = {
  es: ES_CORE,
} as const;

export type TranslationKey = keyof typeof ES_CORE | string;

export type LazyLocale = Exclude<AppLanguage, 'es'>;

export async function loadEnterpriseEs(): Promise<Record<string, string>> {
  const mod = await import('./locales/enterprise.es');
  return mod.ENTERPRISE_ES as Record<string, string>;
}

export async function loadLocale(lang: LazyLocale): Promise<Record<string, string>> {
  if (lang === 'en') {
    const [mod, ent] = await Promise.all([
      import('./locales/en'),
      import('./locales/enterprise.en'),
    ]);
    return { ...mod.LOCALE_EN, ...ent.ENTERPRISE_EN } as Record<string, string>;
  }
  const enterprise = await loadEnterpriseEs();
  return { ...ES_CORE, ...enterprise } as Record<string, string>;
}
