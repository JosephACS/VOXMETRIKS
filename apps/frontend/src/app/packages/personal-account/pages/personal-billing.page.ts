import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { PersonalAccountApiService } from '../services/personal-account-api.service';

@Component({
  selector: 'app-personal-billing-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrl: '../personal-account.css',
  template: `
    <div class="vx-enterprise personal-account-page">
      <app-enterprise-page-header
        [title]="'personal.billing.title' | t:lang()"
        [subtitle]="'personal.billing.subtitle' | t:lang()"
      >
        <a routerLink="/account/plans" class="btn btn--secondary">{{
          'personal.nav.plans' | t:lang()
        }}</a>
      </app-enterprise-page-header>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (!items().length) {
        <app-enterprise-empty-state
          [title]="'personal.billing.emptyTitle' | t:lang()"
          [description]="'personal.billing.emptyBody' | t:lang()"
        />
      } @else {
        <app-enterprise-data-table>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'billing.invoices.number' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th>{{ 'common.amount' | t:lang() }}</th>
                <th>{{ 'common.date' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (inv of items(); track $any(inv).id) {
                <tr>
                  <td>{{ $any(inv).invoice_number }}</td>
                  <td><app-enterprise-status-badge [status]="$any(inv).status" /></td>
                  <td>{{ $any(inv).total }} {{ $any(inv).currency }}</td>
                  <td>{{ $any(inv).issued_at || ('common.notAvailable' | t:lang()) }}</td>
                </tr>
              }
            </tbody>
          </table>
        </app-enterprise-data-table>
      }
    </div>
  `,
})
export class PersonalBillingPage implements OnInit {
  private api = inject(PersonalAccountApiService);
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  items = signal<unknown[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.listInvoices().subscribe({
      next: (res) => {
        this.items.set(res.items || []);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
        this.loading.set(false);
      },
    });
  }
}
