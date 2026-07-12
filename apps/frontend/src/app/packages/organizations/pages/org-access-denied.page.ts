import { Component, inject} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-org-access-denied-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-access-denied">
      <h1>{{ 'organizations.accessDenied.title' | t:lang() }}</h1>
      <p class="lede">No tienes permiso para esta acción en la organización activa.</p>
      <div class="org-actions">
        <a class="org-btn org-btn--ghost" routerLink="/discover">Volver</a>
      </div>
    </section>
  `,
})
export class OrgAccessDeniedPageComponent {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
}
