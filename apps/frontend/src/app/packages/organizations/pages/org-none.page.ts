import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-org-none-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-none-page">
      <h1>{{ 'organizations.none.title' | t:lang() }}</h1>
      <p class="lede">{{ 'organizations.none.lede' | t:lang() }}</p>
      <div class="org-card">
        <p>{{ 'organizations.none.hint' | t:lang() }}</p>
        <div class="org-actions">
          <a class="org-btn" routerLink="/organizations/new">{{ 'organizations.create.title' | t:lang() }}</a>
          <a class="org-btn org-btn--ghost" routerLink="/invitations/accept">{{ 'organizations.acceptInvite.title' | t:lang() }}</a>
          <a class="org-btn org-btn--ghost" routerLink="/discover">{{ 'organizations.none.personal' | t:lang() }}</a>
        </div>
      </div>
      @if (ctx.organizations().length) {
        <div class="org-card">
          <h2>{{ 'organizations.none.accessible' | t:lang() }}</h2>
          <ul>
            @for (o of ctx.organizations(); track o.id) {
              <li>
                {{ o.display_name }}
                <span class="org-badge" [class.org-badge--suspended]="o.status !== 'active'">{{ o.status | statusLabel }}</span>
              </li>
            }
          </ul>
        </div>
      }
    </section>
  `,
})
export class OrgNonePageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  readonly ctx = inject(OrganizationContextService);

  ngOnInit(): void {
    if (this.ctx.status() === 'idle') void this.ctx.bootstrap();
  }
}
