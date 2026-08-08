import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { CreditNote, Invoice } from '../models/billing.models';
import { isCreditNoteInvoice } from '../billing-option-filters';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-credit-notes',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise credit-notes-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header [title]="'billing.creditNotes.title' | t:lang()">
          <button type="button" class="btn btn--secondary" (click)="toggleForm()">
            {{ (showForm ? 'billing.creditNotes.cancel' : 'billing.creditNotes.new') | t:lang() }}
          </button>
        </app-enterprise-page-header>

        <p class="muted page-hint">{{ 'billing.creditNotes.hint' | t:lang() }}</p>

        @if (showForm) {
          <app-enterprise-section-card [title]="'billing.creditNotes.new' | t:lang()">
            <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
              <app-enterprise-form-field [label]="'billing.creditNotes.invoice' | t:lang()" [required]="true">
                <select formControlName="invoice_id" class="select">
                  <option [ngValue]="null">{{ 'billing.creditNotes.selectInvoice' | t:lang() }}</option>
                  @for (inv of invoices; track inv.id) {
                    <option [ngValue]="inv.id">
                      {{ inv.invoice_number }} — {{ inv.total | localeMoney:inv.currency }} ({{ inv.status }})
                    </option>
                  }
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.amount' | t:lang()" [required]="true">
                <input type="number" formControlName="amount" step="0.01" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.reason' | t:lang()">
                <input formControlName="reason" class="input" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button type="submit" class="btn btn--primary" [disabled]="form.invalid">
                  {{ 'billing.creditNotes.create' | t:lang() }}
                </button>
              </div>
            </form>
          </app-enterprise-section-card>
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="loadCreditNotes()" />
        }

        @if (!creditNotes.length && !error) {
          <app-enterprise-empty-state
            [title]="'billing.creditNotes.emptyTitle' | t:lang()"
            [description]="'billing.creditNotes.emptyBody' | t:lang()"
            [ctaLabel]="'billing.creditNotes.new' | t:lang()"
            (ctaClick)="toggleForm(true)"
          />
        } @else if (creditNotes.length) {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'billing.creditNotes.number' | t:lang() }}</th>
                  <th>{{ 'billing.creditNotes.invoice' | t:lang() }}</th>
                  <th>{{ 'common.amount' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (cn of creditNotes; track cn.id) {
                  <tr>
                    <td>{{ cn.credit_note_number }}</td>
                    <td>{{ invoiceLabel(cn.invoice_id) }}</td>
                    <td>{{ cn.amount | localeMoney:cn.currency }}</td>
                    <td><app-enterprise-status-badge [status]="cn.status" /></td>
                    <td>
                      @if (cn.status === 'issued') {
                        <button type="button" class="btn btn--sm" (click)="apply(cn.id)">
                          {{ 'billing.creditNotes.apply' | t:lang() }}
                        </button>
                      }
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
export class CreditNotesPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  creditNotes: CreditNote[] = [];
  invoices: Invoice[] = [];
  invoiceById = new Map<number, Invoice>();
  error: string | null = null;
  showForm = false;
  orgId: number | null = null;

  form = this.fb.group({
    invoice_id: [null as number | null, Validators.required],
    amount: [null as number | null, [Validators.required, Validators.min(0.01)]],
    reason: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.loadCreditNotes();
    this.loadInvoices();
  }

  toggleForm(force?: boolean): void {
    this.showForm = force ?? !this.showForm;
    if (this.showForm && !this.invoices.length) this.loadInvoices();
  }

  loadInvoices(): void {
    this.api.listInvoices(this.orgId!, { page_size: 100 }).subscribe({
      next: (res) => {
        const items = res.items || [];
        this.invoices = items.filter(isCreditNoteInvoice);
        this.invoiceById = new Map(items.map((i) => [i.id, i]));
      },
      error: () => {
        this.invoices = [];
      },
    });
  }

  loadCreditNotes(): void {
    this.api.listCreditNotes(this.orgId!).subscribe({
      next: (res) => (this.creditNotes = res.items),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.loadFailed')),
    });
  }

  invoiceLabel(invoiceId: number): string {
    const inv = this.invoiceById.get(invoiceId);
    return inv?.invoice_number || String(invoiceId);
  }

  submit(): void {
    if (this.form.invalid) return;
    this.api.createCreditNote(this.orgId!, this.form.value).subscribe({
      next: () => {
        this.showForm = false;
        this.form.reset({ invoice_id: null, amount: null, reason: '' });
        this.loadCreditNotes();
      },
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.createFailed')),
    });
  }

  apply(id: number): void {
    this.api.applyCreditNote(this.orgId!, id).subscribe({
      next: () => this.loadCreditNotes(),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.actionFailed')),
    });
  }
}
