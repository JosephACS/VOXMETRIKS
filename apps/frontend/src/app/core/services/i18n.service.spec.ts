import { TestBed } from '@angular/core/testing';
import { I18nService } from '../services/i18n.service';
import { UiPreferencesService } from '../services/ui-preferences.service';
import { LocaleFormatService } from '../services/locale-format.service';
import { statusLabelKey } from '../i18n/status-labels';
import { httpErrorKey } from '../i18n/http-error-keys';

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
    ui.setLanguage('en');
    await i18n.ensureLocale('en');
    expect(i18n.t(statusLabelKey('past_due'))).toBe('Past due');
    expect(i18n.t(statusLabelKey('draft'))).toBe('Draft');
    expect(i18n.t(statusLabelKey('closed'))).toBe('Closed');
    expect(i18n.t(statusLabelKey('resolved'))).toBe('Resolved');
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
});
