import { TestBed } from '@angular/core/testing';
import { I18nService } from '../services/i18n.service';
import { UiPreferencesService } from '../services/ui-preferences.service';
import { LocaleFormatService } from '../services/locale-format.service';
import { statusLabelKey } from '../i18n/status-labels';
import { httpErrorKey } from '../i18n/http-error-keys';
import {
  formatUpdatedWeek,
  resolveSectionSubtitle,
  resolveSectionTitle,
  resolveSystemCode,
  translateReasonCode,
} from '../i18n/system-labels';

describe('I18nService', () => {
  const STORAGE_KEY = 'voxmetrik_ui_prefs';

  beforeEach(() => {
    localStorage.removeItem(STORAGE_KEY);
    TestBed.configureTestingModule({
      providers: [UiPreferencesService, I18nService, LocaleFormatService],
    });
  });

  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it('defaults to Spanish', () => {
    const ui = TestBed.inject(UiPreferencesService);
    const i18n = TestBed.inject(I18nService);
    expect(ui.language()).toBe('es');
    expect(i18n.t('billing.invoices.title')).toBe('Facturas');
  });

  it('switches to English after locale load', async () => {
    const ui = TestBed.inject(UiPreferencesService);
    const i18n = TestBed.inject(I18nService);
    ui.setLanguage('en');
    await i18n.ensureLocale('en');
    expect(i18n.t('billing.invoices.title')).toBe('Invoices');
  });

  it('persists language in localStorage', () => {
    const ui = TestBed.inject(UiPreferencesService);
    ui.setLanguage('en');
    const raw = localStorage.getItem(STORAGE_KEY);
    expect(raw).toBeTruthy();
    expect(JSON.parse(raw!).language).toBe('en');
  });

  it('falls back to Spanish / generic — never shows raw keys', () => {
    const i18n = TestBed.inject(I18nService);
    const out = i18n.t('definitely.missing.key.xyz');
    expect(out).not.toContain('definitely.missing');
    expect(out.length).toBeGreaterThan(0);
  });

  it('translates status codes via central map', async () => {
    const ui = TestBed.inject(UiPreferencesService);
    const i18n = TestBed.inject(I18nService);
    expect(statusLabelKey('past_due')).toBe('status.past_due');
    expect(i18n.t(statusLabelKey('active'))).toBe('Activa');
    expect(i18n.t(statusLabelKey('paid'))).toBe('Pagada');
    expect(statusLabelKey('not_found')).toBe('status.not_found');
    expect(i18n.t(statusLabelKey('not_found'))).toBe('No encontrada');
    ui.setLanguage('en');
    await i18n.ensureLocale('en');
    expect(i18n.t(statusLabelKey('past_due'))).toBe('Past due');
    expect(i18n.t(statusLabelKey('draft'))).toBe('Draft');
    expect(i18n.t(statusLabelKey('closed'))).toBe('Closed');
    expect(i18n.t(statusLabelKey('resolved'))).toBe('Resolved');
    expect(i18n.t(statusLabelKey('active'))).toBe('Active');
    expect(i18n.t(statusLabelKey('not_found'))).toBe('Not found');
    expect(i18n.t(statusLabelKey('totally_unknown_xyz'))).toBe(i18n.t('common.notAvailable'));
  });

  it('maps HTTP errors to translated messages', () => {
    const i18n = TestBed.inject(I18nService);
    expect(httpErrorKey(401)).toBe('httpError.401');
    expect(i18n.t(httpErrorKey(403))).toContain('permiso');
    expect(i18n.t(httpErrorKey(999))).toBe(i18n.t('httpError.generic'));
  });

  it('formats money and dates by locale', async () => {
    const ui = TestBed.inject(UiPreferencesService);
    const fmt = TestBed.inject(LocaleFormatService);
    const esMoney = fmt.formatMoney(99, 'USD');
    expect(esMoney).toMatch(/99/);
    expect(esMoney).toMatch(/USD|\$/);
    // Spanish uses comma decimal
    expect(esMoney.includes(',') || esMoney.includes('.')).toBe(true);

    ui.setLanguage('en');
    const enMoney = fmt.formatMoney(1234.56, 'USD');
    expect(enMoney).toMatch(/1,234\.56|1234\.56/);

    const d = new Date('2024-06-15T12:00:00Z');
    ui.setLanguage('es');
    const esDate = fmt.formatDate(d);
    expect(esDate.length).toBeGreaterThan(0);
    ui.setLanguage('en');
    const enDate = fmt.formatDate(d);
    expect(enDate.length).toBeGreaterThan(0);
  });

  it('translates smart system codes without hardcoding language branches', async () => {
    const ui = TestBed.inject(UiPreferencesService);
    const i18n = TestBed.inject(I18nService);
    const t = (k: string, p?: Record<string, string | number>) => i18n.t(k, p);

    expect(resolveSystemCode('discover_weekly')).toBe('discover_weekly');
    expect(resolveSystemCode(null, 'Discover Weekly')).toBe('discover_weekly');
    expect(resolveSectionTitle({ code: 'discover_weekly' }, t)).toBe('Descubrimiento semanal');
    expect(resolveSectionTitle({ code: 'daily_mix_rock' }, t)).toBe('Mix diario de rock');
    expect(resolveSectionTitle({ code: 'daily_mix_chill' }, t)).toBe('Mix diario relajante');
    expect(formatUpdatedWeek('2026-W29', t)).toBe('Actualizado: semana 29 de 2026');
    expect(translateReasonCode('high_popularity', t)).toBe('Popularidad alta');
    expect(
      resolveSectionTitle(
        { code: 'because_listened', title_params: { name: 'Bohemian Rhapsody' } },
        t,
      ),
    ).toBe('Porque escuchaste Bohemian Rhapsody');
    // Proper names stay as-is when no system code
    expect(resolveSectionTitle({ title: 'Mis favoritos 2024' }, t)).toBe('Mis favoritos 2024');

    ui.setLanguage('en');
    await i18n.ensureLocale('en');
    expect(resolveSectionTitle({ code: 'discover_weekly' }, t)).toBe('Discover Weekly');
    expect(resolveSectionTitle({ code: 'daily_mix_pop' }, t)).toBe('Daily Mix Pop');
    expect(formatUpdatedWeek('2026-W29', t)).toBe('Updated: week 29 of 2026');
    expect(translateReasonCode('high_popularity', t)).toBe('High popularity');
    expect(
      resolveSectionSubtitle({ code: 'discover_weekly', week: '2026-W29' }, t),
    ).toBe('Updated: week 29 of 2026');
  });
});
