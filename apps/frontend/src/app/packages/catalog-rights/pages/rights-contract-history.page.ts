import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { RightsStatusHistoryEntry } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-rights-contract-history',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="vx-enterprise rights-contract-history-page">
      <a [routerLink]="['/catalog-rights/contracts', contractId]">&larr; Back to contract</a>
      <h1>Contract #{{ contractId }} — {{ 'artists.history.title' | t:lang() }}</h1>

      @if (error) {
        <p class="error">{{ error }}</p>
      }

      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (history.length === 0) {
        <p>{{ 'artists.history.empty' | t:lang() }}</p>
      } @else {
        <ul class="timeline">
          @for (h of history; track h.id) {
            <li class="timeline-entry">
              <span class="timeline-dot"></span>
              <div class="timeline-body">
                <strong>{{ h.from_status ?? 'created' }} &rarr; {{ h.to_status }}</strong>
                <p class="reason">{{ h.reason ?? 'No reason recorded.' }}</p>
                <p class="meta">{{ h.at | date:'short' }} — actor #{{ h.actor ?? 'system' }}</p>
              </div>
            </li>
          }
        </ul>
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

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  get contractId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.api.getContractHistory(this.orgId, this.contractId).subscribe({
      next: (items) => {
        this.history = items;
        this.loading = false;
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? 'Error loading contract history';
      },
    });
  }
}
