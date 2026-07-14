import { Injectable, inject } from '@angular/core';
import { UiPreferencesService } from './ui-preferences.service';

/**
 * Locale-aware date/number/currency formatting via Intl.
 * Does not alter stored values — presentation only.
 */
@Injectable({ providedIn: 'root' })
export class LocaleFormatService {
  private readonly ui = inject(UiPreferencesService);

  private localeTag(): string {
    return this.ui.language() === 'en' ? 'en-US' : 'es-ES';
  }

  formatDate(
    value: string | Date | null | undefined,
    options: Intl.DateTimeFormatOptions = { dateStyle: 'medium' },
  ): string {
    if (value == null || value === '') return '';
    const d = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return new Intl.DateTimeFormat(this.localeTag(), options).format(d);
  }

  formatDateTime(value: string | Date | null | undefined): string {
    return this.formatDate(value, { dateStyle: 'medium', timeStyle: 'short' });
  }

  formatNumber(value: number | string | null | undefined, fractionDigits = 2): string {
    if (value == null || value === '') return '';
    const n = typeof value === 'number' ? value : Number(value);
    if (!Number.isFinite(n)) return String(value);
    return new Intl.NumberFormat(this.localeTag(), {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(n);
  }

  /** e.g. $99,00 USD (es) or $99.00 USD (en) — never "99,00 US$ USD". */
  formatMoney(amount: number | string | null | undefined, currency = 'USD'): string {
    if (amount == null || amount === '') return '';
    const n = typeof amount === 'number' ? amount : Number(amount);
    if (!Number.isFinite(n)) return String(amount);
    const code = (currency || 'USD').toUpperCase();
    const numberOnly = new Intl.NumberFormat(this.localeTag(), {
      style: 'decimal',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(n);
    return `$${numberOnly} ${code}`;
  }
}
