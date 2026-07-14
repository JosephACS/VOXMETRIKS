import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-access-denied-page',
  standalone: true,
  imports: [RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-access-denied-page">
      <app-enterprise-page-header
        [title]="'crm.accessDenied.title' | t:lang()"
        [subtitle]="'crm.accessDenied.body' | t:lang()"
      />

      <app-enterprise-section-card>
        <p>{{ 'crm.accessDenied.hint' | t:lang() }}</p>
        <p class="muted">{{ 'crm.accessDenied.rolesHint' | t:lang() }}</p>
        <app-enterprise-action-bar>
          <a class="btn btn--ghost" routerLink="/discover">{{ 'crm.accessDenied.home' | t:lang() }}</a>
          <a class="btn btn--ghost" routerLink="/settings">{{ 'crm.accessDenied.profile' | t:lang() }}</a>
        </app-enterprise-action-bar>
      </app-enterprise-section-card>
    </div>
  `,
})
export class CrmAccessDeniedPageComponent {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
}
