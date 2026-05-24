import { Pipe, PipeTransform, inject } from '@angular/core';
import { I18nService } from '../../core/services/i18n.service';
import { TranslationKey } from '../../core/i18n/translations';

@Pipe({
  name: 't',
  standalone: true,
  pure: false,
})
export class TranslatePipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(key: TranslationKey | string, params?: Record<string, string | number>): string {
    this.i18n.tick();
    return this.i18n.t(key, params);
  }
}
