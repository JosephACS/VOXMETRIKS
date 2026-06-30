import { Pipe, PipeTransform, inject } from '@angular/core';
import { I18nService } from '../../core/services/i18n.service';
import { TranslationKey } from '../../core/i18n/translations';

type Params = Record<string, string | number>;

/**
 * Pure translate pipe — pass `lang()` as the last argument so templates re-run on locale change.
 * Examples: `{{ 'home.title' | t:lang() }}` or `{{ 'k' | t:{ n: 1 }:lang() }}`
 */
@Pipe({
  name: 't',
  standalone: true,
  pure: true,
})
export class TranslatePipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(
    key: TranslationKey | string,
    paramsOrLang?: Params | string | number | null,
    langTrigger?: string | number | null,
  ): string {
    let params: Params | undefined;
    if (paramsOrLang !== null && typeof paramsOrLang === 'object') {
      params = paramsOrLang as Params;
      void langTrigger;
    } else {
      void (paramsOrLang ?? langTrigger);
    }
    return this.i18n.t(key, params);
  }
}
