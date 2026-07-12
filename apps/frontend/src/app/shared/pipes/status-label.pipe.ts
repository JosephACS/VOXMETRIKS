import { Pipe, PipeTransform, inject } from '@angular/core';
import { I18nService } from '../../core/services/i18n.service';
import { statusLabelKey } from '../../core/i18n/status-labels';

/** Translate domain status codes without changing stored values. */
@Pipe({ name: 'statusLabel', standalone: true, pure: false })
export class StatusLabelPipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(code: string | null | undefined): string {
    void this.i18n.lang(); // re-run on language change
    return this.i18n.t(statusLabelKey(code));
  }
}
