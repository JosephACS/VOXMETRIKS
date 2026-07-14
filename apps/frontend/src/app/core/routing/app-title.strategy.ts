import { Injectable, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';
import { I18nService } from '../services/i18n.service';

@Injectable()
export class AppTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);
  private readonly i18n = inject(I18nService);

  override updateTitle(snapshot: RouterStateSnapshot): void {
    const routeTitle = this.buildTitle(snapshot);
    if (!routeTitle) {
      this.title.setTitle('VOXMETRIK — Music Intelligence Platform');
      return;
    }
    // Route titles are often human-readable (ES/EN literals). Only look up dotted i18n keys.
    const looksLikeKey = /^[a-z0-9]+(?:\.[a-z0-9_-]+)+$/i.test(routeTitle);
    const label = looksLikeKey ? this.i18n.t(routeTitle) : routeTitle;
    const missing = this.i18n.t('common.missingTranslation');
    const display = looksLikeKey && (label === missing || label === routeTitle) ? routeTitle : label;
    this.title.setTitle(`${display} | VOXMETRIK`);
  }
}
