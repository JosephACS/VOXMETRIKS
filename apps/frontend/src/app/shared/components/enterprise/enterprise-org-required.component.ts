import { ChangeDetectionStrategy, Component, inject, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { OrgSelectorBridgeService } from '../../../packages/organizations/services/org-selector-bridge.service';

@Component({
  selector: 'app-enterprise-org-required',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, TranslatePipe],
  template: `
    <div class="empty-state ent-org-required" role="status">
      <div class="ent-org-required__icon" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 21h18" />
          <path d="M5 21V7l7-4 7 4v14" />
          <path d="M9 21v-6h6v6" />
          <path d="M9 9h.01" />
          <path d="M15 9h.01" />
          <path d="M9 13h.01" />
          <path d="M15 13h.01" />
        </svg>
      </div>
      <h2 class="ent-org-required__title">
        {{ 'organizations.orgRequired.title' | t:lang() }}
      </h2>
      <p class="ent-org-required__body">
        {{ 'organizations.orgRequired.body' | t:lang() }}
      </p>
      <div class="ent-org-required__actions">
        <button type="button" class="btn btn--primary" (click)="onOpenSelector()">
          {{ 'organizations.orgRequired.openSelector' | t:lang() }}
        </button>
        <a routerLink="/organizations/new" class="btn btn--secondary">
          {{ 'organizations.orgRequired.createOrg' | t:lang() }}
        </a>
      </div>
    </div>
  `,
})
export class EnterpriseOrgRequiredComponent {
  private readonly i18n = inject(I18nService);
  private readonly bridge = inject(OrgSelectorBridgeService);
  readonly lang = this.i18n.lang;
  readonly openSelector = output<void>();

  onOpenSelector(): void {
    this.openSelector.emit();
    this.bridge.requestOpen();
  }
}
