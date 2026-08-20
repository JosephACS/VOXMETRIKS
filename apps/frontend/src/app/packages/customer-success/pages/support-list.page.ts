import { Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-support-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise support-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'support.list.title' | t:lang()"
          [subtitle]="'support.list.subtitle' | t:lang()"
        >
          <a routerLink="/customer-success" class="btn btn--secondary">
            {{ 'customerSuccess.dashboard.title' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'support.list.create' | t:lang()">
          <form class="form-grid" (ngSubmit)="create()" id="support-create-form">
            <app-enterprise-form-field [label]="'support.list.subject' | t:lang()" [required]="true">
              <input [(ngModel)]="subject" name="subject" class="input" #subjectInput />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="busy || !subject">
                {{ 'support.list.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!cases.length) {
          <app-enterprise-empty-state
            [title]="'support.list.emptyTitle' | t:lang()"
            [description]="'support.list.emptyBody' | t:lang()"
            [ctaLabel]="'support.list.create' | t:lang()"
            (ctaClick)="focusCreate()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'support.list.subject' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (c of cases; track $index) {
                  <tr>
                    <td>
                      <a [routerLink]="['/support', $any(c).id]">{{ $any(c).subject }}</a>
                    </td>
                    <td>
                      <app-enterprise-status-badge [status]="$any(c).status" />
                      / {{ $any(c).priority }}
                    </td>
                    <td>
                      <a [routerLink]="['/support', $any(c).id]" class="btn btn--ghost btn--sm">
                        {{ 'common.view' | t:lang() }}
                      </a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      }
    </div>
  `,
})
export class SupportListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);
  @ViewChild('subjectInput') subjectInput?: ElementRef<HTMLInputElement>;
  orgId: number | null = null;
  cases: unknown[] = [];
  subject = '';
  error = '';
  loading = false;
  busy = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.reload();
  }

  focusCreate(): void {
    const el = this.subjectInput?.nativeElement;
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.focus();
    } else {
      document.getElementById('support-create-form')?.scrollIntoView({ behavior: 'smooth' });
    }
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = '';
    this.api.listCases(this.orgId).subscribe({
      next: (c) => {
        this.cases = c || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('support.list.loadFailed');
        this.loading = false;
      },
    });
  }

  create(): void {
    if (!this.orgId || !this.subject) return;
    this.busy = true;
    this.api.createCase(this.orgId, this.subject).subscribe({
      next: () => {
        this.subject = '';
        this.busy = false;
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('support.list.createFailed');
        this.busy = false;
      },
    });
  }
}
