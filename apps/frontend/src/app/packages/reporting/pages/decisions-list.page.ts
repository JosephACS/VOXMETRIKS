import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { BusinessDecision } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-decisions-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  template: `
    <div class="vx-enterprise page">
      <h1>{{ 'decisions.list.title' | t:lang() }}</h1>
      <nav class="subnav">
        <a routerLink="/reports">Reports</a> |
        <a routerLink="/business-decisions">Decisions</a>
      </nav>
      @if (!orgId) { <p class="error">Select an organization context.</p> }
      @else {
        <section>
          <input [(ngModel)]="title" placeholder="title" />
          <input [(ngModel)]="proposal" placeholder="proposal" />
          <button type="button" (click)="create()" [disabled]="busy">{{ 'decisions.list.record' | t:lang() }}</button>
        </section>
        @if (loading) { <p>{{ 'common.loading' | t:lang() }}</p> }
        @else if (error) { <p class="error">{{ error }}</p> }
        @else if (!items.length) { <p>{{ 'decisions.list.empty' | t:lang() }}</p> }
        @else {
          <ul>
            @for (d of items; track d.id) {
              <li>
                <a [routerLink]="['/business-decisions', d.id]">{{ d.title }}</a>
                — {{ d.status }}
              </li>
            }
          </ul>
        }
      }
    </div>
  `,
})
export class DecisionsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  items: BusinessDecision[] = [];
  title = '';
  proposal = '';
  loading = false;
  busy = false;
  error = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (this.orgId) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.api.listDecisions(this.orgId).subscribe({
      next: (p) => {
        this.items = p.items || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Failed to load';
        this.loading = false;
      },
    });
  }

  create(): void {
    if (!this.orgId || !this.title || !this.proposal) return;
    this.busy = true;
    this.api.createDecision(this.orgId, { title: this.title, proposal: this.proposal }).subscribe({
      next: () => {
        this.busy = false;
        this.title = '';
        this.proposal = '';
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Create failed';
        this.busy = false;
      },
    });
  }
}
