import { Pipe, PipeTransform, inject } from '@angular/core';
import { LocaleFormatService } from '../../core/services/locale-format.service';
import { I18nService } from '../../core/services/i18n.service';

@Pipe({ name: 'localeMoney', standalone: true, pure: false })
export class LocaleMoneyPipe implements PipeTransform {
  private readonly fmt = inject(LocaleFormatService);
  private readonly i18n = inject(I18nService);

  transform(amount: number | string | null | undefined, currency = 'USD'): string {
    void this.i18n.lang();
    const out = this.fmt.formatMoney(amount, currency);
    return out || this.i18n.t('common.notAvailable');
  }
}

@Pipe({ name: 'localeDate', standalone: true, pure: false })
export class LocaleDatePipe implements PipeTransform {
  private readonly fmt = inject(LocaleFormatService);
  private readonly i18n = inject(I18nService);

  transform(value: string | Date | null | undefined, withTime = false): string {
    void this.i18n.lang();
    const out = withTime ? this.fmt.formatDateTime(value) : this.fmt.formatDate(value);
    return out || this.i18n.t('common.notAvailable');
  }
}
