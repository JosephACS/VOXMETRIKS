import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CustomerConversion } from '../models/crm.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

type WizardStep = 'view' | 'confirm-link' | 'claim';

@Component({
  selector: 'app-crm-conversion-wizard-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-conversion-wizard-page">
      <app-enterprise-page-header [title]="('crm.conversion.title' | t:lang()) + ' #' + conversionId">
        <a class="btn btn--ghost" routerLink="/crm/opportunities">
          ← {{ 'crm.conversion.backOpportunities' | t:lang() }}
        </a>
        @if (conv()) {
          <app-enterprise-status-badge [status]="conv()!.status" />
        }
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      <div class="crm-wizard-steps">
        <span class="crm-wizard-step" [class.crm-wizard-step--active]="step === 'view'">
          {{ 'crm.conversion.step1' | t:lang() }}
        </span>
        <span
          class="crm-wizard-step"
          [class.crm-wizard-step--active]="step === 'confirm-link'"
          [class.crm-wizard-step--done]="step !== 'confirm-link'"
        >
          {{ 'crm.conversion.step2' | t:lang() }}
        </span>
        <span
          class="crm-wizard-step"
          [class.crm-wizard-step--active]="step === 'claim'"
          [class.crm-wizard-step--done]="step !== 'claim'"
        >
          {{ 'crm.conversion.step3' | t:lang() }}
        </span>
      </div>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (conv()) {
        @if (step === 'view') {
          <app-enterprise-section-card [title]="'crm.conversion.status' | t:lang()">
            <div class="form-grid" style="font-size: 0.875rem">
              <div>
                <dt class="muted">{{ 'crm.contract.opportunity' | t:lang() }}</dt>
                <dd>#{{ conv()!.opportunity_id }}</dd>
              </div>
              <div>
                <dt class="muted">{{ 'crm.conversion.mode' | t:lang() }}</dt>
                <dd>{{ conv()!.mode }}</dd>
              </div>
              <div>
                <dt class="muted">{{ 'common.status' | t:lang() }}</dt>
                <dd><app-enterprise-status-badge [status]="conv()!.status" /></dd>
              </div>
              @if (conv()!.organization_id) {
                <div>
                  <dt class="muted">{{ 'crm.conversion.linkedOrg' | t:lang() }}</dt>
                  <dd>#{{ conv()!.organization_id }}</dd>
                </div>
              }
              @if (conv()!.contact_id) {
                <div>
                  <dt class="muted">{{ 'crm.conversion.contact' | t:lang() }}</dt>
                  <dd>#{{ conv()!.contact_id }}</dd>
                </div>
              }
              @if (conv()!.claim_token_expires_at) {
                <div>
                  <dt class="muted">{{ 'crm.conversion.tokenExpires' | t:lang() }}</dt>
                  <dd>{{ conv()!.claim_token_expires_at | localeDate:true }}</dd>
                </div>
              }
              @if (conv()!.completed_at) {
                <div>
                  <dt class="muted">{{ 'crm.conversion.completed' | t:lang() }}</dt>
                  <dd>{{ conv()!.completed_at | localeDate:true }}</dd>
                </div>
              }
              @if (conv()!.failure_reason) {
                <div>
                  <dt class="muted">{{ 'crm.conversion.failureReason' | t:lang() }}</dt>
                  <dd>{{ conv()!.failure_reason }}</dd>
                </div>
              }
              <div>
                <dt class="muted">{{ 'common.created' | t:lang() }}</dt>
                <dd>{{ conv()!.created_at | localeDate:true }}</dd>
              </div>
            </div>
          </app-enterprise-section-card>

          @if (conv()!.status === 'completed' && conv()!.organization_id) {
            <app-enterprise-section-card [title]="'crm.conversion.nextStep' | t:lang()">
              <p class="muted">{{ 'crm.conversion.continuePlanDesc' | t:lang() }}</p>
              <app-enterprise-action-bar>
                <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="continueToPlan()">
                  {{ 'crm.conversion.continuePlan' | t:lang() }}
                </button>
              </app-enterprise-action-bar>
            </app-enterprise-section-card>
          }

          @if (conv()!.status === 'pending' || conv()!.status === 'prepared' || conv()!.status === 'awaiting_customer_claim') {
            <app-enterprise-section-card [title]="'crm.conversion.continueProcess' | t:lang()">
              <app-enterprise-action-bar>
                @if (conv()!.mode === 'link_existing' && (conv()!.status === 'pending' || conv()!.status === 'prepared')) {
                  <button type="button" class="btn btn--primary" (click)="step = 'confirm-link'">
                    {{ 'crm.conversion.confirmLinkOwner' | t:lang() }}
                  </button>
                }
                @if (conv()!.mode === 'create_org' && conv()!.status === 'awaiting_customer_claim') {
                  <button type="button" class="btn btn--primary" (click)="step = 'claim'">
                    {{ 'crm.conversion.claimWithToken' | t:lang() }}
                  </button>
                }
              </app-enterprise-action-bar>
            </app-enterprise-section-card>
          }

          @if (oneTimeClaimToken()) {
            <app-enterprise-section-card [title]="'crm.conversion.oneTimeTokenTitle' | t:lang()">
              <div class="alert alert--warn" role="status">{{ 'crm.conversion.oneTimeTokenBody' | t:lang() }}</div>
              <p class="crm-token-mono" data-testid="crm-claim-token-once">{{ oneTimeClaimToken() }}</p>
              <app-enterprise-action-bar>
                <button type="button" class="btn btn--secondary" (click)="copyClaimToken()">
                  {{ 'crm.conversion.copyToken' | t:lang() }}
                </button>
                <button type="button" class="btn btn--primary" (click)="useClaimToken()">
                  {{ 'crm.conversion.claimWithToken' | t:lang() }}
                </button>
              </app-enterprise-action-bar>
            </app-enterprise-section-card>
          }
        }

        @if (step === 'confirm-link') {
          <app-enterprise-section-card [title]="'crm.conversion.confirmLink' | t:lang()">
            <p class="muted">{{ 'crm.conversion.confirmLinkDesc' | t:lang() }}</p>
            <form class="form-grid">
              <app-enterprise-form-field [label]="'crm.conversion.orgId' | t:lang()" [required]="true">
                <input
                  class="input"
                  [(ngModel)]="linkOrgId"
                  name="linkOrgId"
                  type="number"
                  min="1"
                  [placeholder]="'crm.conversion.orgIdPlaceholder' | t:lang()"
                />
              </app-enterprise-form-field>
              <app-enterprise-action-bar>
                <button type="button" class="btn btn--primary" [disabled]="!linkOrgId || saving()" (click)="confirmLink()">
                  {{ (saving() ? 'common.processing' : 'crm.conversion.confirmLink') | t:lang() }}
                </button>
                <button type="button" class="btn btn--ghost" (click)="step = 'view'">
                  {{ 'common.cancel' | t:lang() }}
                </button>
              </app-enterprise-action-bar>
            </form>
          </app-enterprise-section-card>
        }

        @if (step === 'claim') {
          <app-enterprise-section-card [title]="'crm.conversion.claim' | t:lang()">
            <div class="alert alert--warn" role="status">{{ 'crm.conversion.tokenWarning' | t:lang() }}</div>
            <form class="form-grid">
              <app-enterprise-form-field [label]="'crm.conversion.claimTokenLabel' | t:lang()" [required]="true">
                <input
                  class="input"
                  [(ngModel)]="claimToken"
                  name="claimToken"
                  type="password"
                  autocomplete="off"
                />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'crm.conversion.orgName' | t:lang()" [required]="true">
                <input class="input" [(ngModel)]="claimOrgName" name="claimOrgName" required />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'crm.conversion.orgSlug' | t:lang()" [required]="true">
                <input class="input" [(ngModel)]="claimOrgSlug" name="claimOrgSlug" required placeholder="mi-empresa" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'crm.conversion.orgType' | t:lang()">
                <select class="select" [(ngModel)]="claimOrgType" name="claimOrgType">
                  <option value="business">{{ 'crm.conversion.orgTypeBusiness' | t:lang() }}</option>
                  <option value="individual">{{ 'crm.conversion.orgTypeIndividual' | t:lang() }}</option>
                  <option value="nonprofit">{{ 'crm.conversion.orgTypeNonprofit' | t:lang() }}</option>
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'crm.conversion.timezone' | t:lang()">
                <input class="input" [(ngModel)]="claimTimezone" name="claimTimezone" placeholder="America/Guayaquil" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.currency' | t:lang()">
                <input class="input" [(ngModel)]="claimCurrency" name="claimCurrency" maxlength="3" placeholder="USD" />
              </app-enterprise-form-field>
              <app-enterprise-action-bar>
                <button
                  type="button"
                  class="btn btn--primary"
                  [disabled]="!claimToken || !claimOrgName || !claimOrgSlug || saving()"
                  (click)="claim()"
                >
                  {{ (saving() ? 'common.processing' : 'crm.conversion.claim') | t:lang() }}
                </button>
                <button type="button" class="btn btn--ghost" (click)="step = 'view'">
                  {{ 'common.cancel' | t:lang() }}
                </button>
              </app-enterprise-action-bar>
            </form>
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
})
export class CrmConversionWizardPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly orgCtx = inject(OrganizationContextService);

  conversionId = 0;
  step: WizardStep = 'view';

  linkOrgId: number | null = null;
  claimToken = '';
  claimOrgName = '';
  claimOrgSlug = '';
  claimOrgType = 'business';
  claimTimezone = 'UTC';
  claimCurrency = 'USD';

  readonly conv = signal<CustomerConversion | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  /** Raw claim token from prepare navigation state (shown once). */
  readonly oneTimeClaimToken = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.conversionId = Number(this.route.snapshot.paramMap.get('id'));
    const nav = this.router.getCurrentNavigation();
    const state = (nav?.extras?.state ?? history.state) as {
      claimToken?: string;
      claimTokenNote?: string;
    } | null;
    const token = state?.claimToken?.trim();
    if (token) {
      this.oneTimeClaimToken.set(token);
      this.claimToken = token;
    }
    await this.load();
  }

  copyClaimToken(): void {
    const token = this.oneTimeClaimToken();
    if (!token || typeof navigator === 'undefined' || !navigator.clipboard?.writeText) return;
    void navigator.clipboard.writeText(token);
    this.success.set(this.i18n.t('crm.conversion.tokenCopied'));
  }

  useClaimToken(): void {
    const token = this.oneTimeClaimToken();
    if (token) this.claimToken = token;
    this.step = 'claim';
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const c = await firstValueFrom(this.api.getConversion(this.conversionId));
      this.conv.set(c);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar conversión');
    } finally {
      this.loading.set(false);
    }
  }

  async confirmLink(): Promise<void> {
    if (!this.linkOrgId) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.confirmLinkConversion(this.conversionId, this.linkOrgId));
      this.conv.set(c);
      this.step = 'view';
      this.success.set('Enlace confirmado. Conversión completada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al confirmar enlace');
    } finally {
      this.saving.set(false);
    }
  }

  async claim(): Promise<void> {
    if (!this.claimToken || !this.claimOrgName || !this.claimOrgSlug) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(
        this.api.claimConversion(
          this.conversionId,
          this.claimToken,
          this.claimOrgName,
          this.claimOrgSlug,
          this.claimOrgType,
          this.claimTimezone,
          this.claimCurrency,
        ),
      );
      this.conv.set(c);
      this.claimToken = '';
      this.step = 'view';
      this.success.set('Conversión reclamada. Organización creada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al reclamar conversión');
    } finally {
      this.saving.set(false);
    }
  }

  async continueToPlan(): Promise<void> {
    const c = this.conv();
    const orgId = c?.organization_id;
    if (!orgId) {
      this.error.set('La conversión no tiene organización vinculada.');
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    try {
      await this.orgCtx.activate(orgId);
      await this.router.navigate(['/subscriptions/select-plan'], {
        queryParams: { organization_id: orgId, conversionId: this.conversionId },
      });
    } catch (e) {
      this.error.set(e instanceof Error ? e.message : 'No se pudo activar la organización');
    } finally {
      this.saving.set(false);
    }
  }
}
