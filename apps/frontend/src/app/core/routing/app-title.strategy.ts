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
    const translatedTitle = routeTitle ? this.i18n.t(routeTitle) : '';
    this.title.setTitle(
      translatedTitle
        ? `${translatedTitle} | VOXMETRIK`
        : 'VOXMETRIK — Music Intelligence Platform',
    );
  }
}
