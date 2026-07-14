import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';
import { Organization } from '../models/organization.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';

@Component({
  selector: 'app-org-none-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, StatusLabelPipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-none-page">
      <h1>{{ 'organizations.none.title' | t:lang() }}</h1>
      <p class="lede">{{ 'organizations.none.lede' | t:lang() }}</p>
      <div class="org-card">
        <p>{{ 'organizations.none.hint' | t:lang() }}</p>
        <div class="org-actions">
          <a class="org-btn" routerLink="/organizations/new">{{ 'organizations.create.title' | t:lang() }}</a>
          <a class="org-btn org-btn--ghost" routerLink="/invitations/accept">{{
            'organizations.acceptInvite.title' | t:lang()
          }}</a>
          <a class="org-btn org-btn--ghost" routerLink="/discover">{{
            'organizations.none.personal' | t:lang()
          }}</a>
        </div>
      </div>
      @if (ctx.organizations().length) {
        <div class="org-card">
          <h2>{{ 'organizations.none.accessible' | t:lang() }}</h2>
          <ul class="org-none-list">
            @for (o of ctx.organizations(); track o.id) {
              <li>
                <button type="button" class="org-btn org-btn--ghost" (click)="activateOrg(o)">
                  {{ o.display_name }}
                </button>
                <span class="org-badge" [class.org-badge--suspended]="o.status !== 'active'">{{
                  o.status | statusLabel
                }}</span>
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
  private readonly router = inject(Router);

  async ngOnInit(): Promise<void> {
    await this.ctx.ensureReady();
    // Contradictory state: Demo selected / active but URL is /organizations/none.
    // Leave personal-mode page only when there is a real active org id.
    const id = this.ctx.organizationId();
    if (id != null) {
      await this.router.navigate(['/organizations', id, 'settings'], { replaceUrl: true });
    }
  }

  async activateOrg(o: Organization): Promise<void> {
    if (o.status === 'closed') {
      await this.router.navigate(['/organizations/closed']);
      return;
    }
    if (o.status === 'suspended_by_platform') {
      await this.router.navigate(['/organizations/suspended']);
      return;
    }
    try {
      await this.ctx.activate(o.id);
      await this.router.navigate(['/organizations', o.id, 'settings']);
    } catch {
      /* error surfaced on context */
    }
  }
}
