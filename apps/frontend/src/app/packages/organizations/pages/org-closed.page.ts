import { Component, inject} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-org-closed-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-closed">
      <h1>{{ 'organizations.closed.title' | t:lang() }} o contexto inválido</h1>
      <p class="lede">
        Esta organización ya no está disponible para operaciones. Puedes cambiar de organización
        o continuar en modo personal.
      </p>
      <div class="org-actions">
        <a class="org-btn org-btn--ghost" routerLink="/organizations/none">Sin organización</a>
        <a class="org-btn org-btn--ghost" routerLink="/discover">Modo personal</a>
      </div>
    </section>
  `,
})
export class OrgClosedPageComponent {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
}
