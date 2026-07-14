import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { RightsStatusHistoryEntry } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-rights-contract-history',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise rights-contract-history-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a [routerLink]="['/catalog-rights/contracts', contractId]" class="back-link">
          {{ 'catalogRights.contractHistory.back' | t:lang() }}
        </a>

        <app-enterprise-page-header
          [title]="('catalogRights.contractHistory.title' | t:lang()) + ' #' + contractId"
        />

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (history.length === 0) {
          <app-enterprise-empty-state [title]="'artists.history.empty' | t:lang()" />
        } @else {
          <app-enterprise-section-card [title]="'catalogRights.contractHistory.title' | t:lang()">
            <ul class="timeline">
              @for (h of history; track h.id) {
                <li class="timeline-entry">
                  <span class="timeline-dot"></span>
                  <div class="timeline-body">
                    <strong>{{ h.from_status ?? 'created' }} → {{ h.to_status }}</strong>
                    <p class="reason">{{ h.reason ?? ('catalogRights.contractHistory.noReason' | t:lang()) }}</p>
                    <p class="meta">
                      {{ h.at | localeDate: true }} — actor #{{ h.actor ?? 'system' }}
                    </p>
                  </div>
                </li>
              }
            </ul>
          </app-enterprise-section-card>
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        }
      }
    </div>
  `,
})
export class RightsContractHistoryPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private route = inject(ActivatedRoute);
  private orgCtx = inject(OrganizationContextService);

  history: RightsStatusHistoryEntry[] = [];
  loading = false;
  error: string | null = null;
  orgId: number | null = null;

  get contractId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.loading = true;
    this.error = null;
    this.api.getContractHistory(orgId, this.contractId).subscribe({
      next: (items) => {
        this.history = items;
        this.loading = false;
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? this.i18n.t('common.failed');
      },
    });
  }
}
