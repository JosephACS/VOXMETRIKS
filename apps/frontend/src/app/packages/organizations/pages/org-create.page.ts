import { Component, ElementRef, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-org-create-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-create-page">
      <h1>{{ 'organizations.create.title' | t:lang() }}</h1>
      <p class="lede">Completa el perfil básico. No se solicita información fiscal en esta etapa.</p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert" #errorBox tabindex="-1">{{ error() }}</div>
      }
      @if (success()) {
        <div class="org-alert org-alert--ok" role="status">Organización creada. Redirigiendo al onboarding…</div>
      }

      <form class="org-card org-form" (ngSubmit)="submit()" novalidate>
        <label>
          Nombre visible *
          <input name="display_name" [(ngModel)]="displayName" required maxlength="200" [disabled]="submitting()" />
        </label>
        <label>
          Nombre legal (opcional)
          <input name="legal_name" [(ngModel)]="legalName" maxlength="200" [disabled]="submitting()" />
        </label>
        <label>
          Slug *
          <input
            name="slug"
            [(ngModel)]="slug"
            required
            pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
            [disabled]="submitting()"
            aria-describedby="slug-help"
          />
          <span id="slug-help" class="org-muted">minúsculas, números y guiones</span>
        </label>
        <label>
          Tipo *
          <select name="organization_type" [(ngModel)]="organizationType" [disabled]="submitting()">
            <option value="label">Label</option>
            <option value="distributor">Distributor</option>
            <option value="publisher">Publisher</option>
            <option value="management">Management</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label>
          País (ISO-2)
          <input name="country_code" [(ngModel)]="countryCode" maxlength="2" [disabled]="submitting()" />
        </label>
        <label>
          Zona horaria *
          <input name="timezone" [(ngModel)]="timezone" required [disabled]="submitting()" />
        </label>
        <label>
          Moneda por defecto *
          <input name="default_currency" [(ngModel)]="defaultCurrency" required maxlength="3" [disabled]="submitting()" />
        </label>
        <label>
          <input type="checkbox" name="activate" [(ngModel)]="activate" [disabled]="submitting()" />
          Activar como organización actual
        </label>
        <div class="org-actions">
          <button class="org-btn" type="submit" [disabled]="submitting() || !displayName.trim() || !slug.trim()">
            {{ submitting() ? ('organizations.create.submitting' | t:lang()) : ('organizations.create.title' | t:lang()) }}
          </button>
          <a class="org-btn org-btn--ghost" routerLink="/organizations/none">Cancelar</a>
        </div>
      </form>
    </section>
  `,
})
export class OrgCreatePageComponent {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  private readonly ctx = inject(OrganizationContextService);
  private readonly router = inject(Router);

  @ViewChild('errorBox') errorBox?: ElementRef<HTMLElement>;

  displayName = '';
  legalName = '';
  slug = '';
  organizationType = 'label';
  countryCode = '';
  timezone = 'UTC';
  defaultCurrency = 'USD';
  activate = true;

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  async submit(): Promise<void> {
    if (this.submitting() || this.success()) return;
    this.submitting.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(
        this.api.create({
          display_name: this.displayName.trim(),
          legal_name: this.legalName.trim() || undefined,
          slug: this.slug.trim().toLowerCase(),
          organization_type: this.organizationType,
          country_code: this.countryCode.trim().toUpperCase() || undefined,
          timezone: this.timezone.trim() || 'UTC',
          default_currency: this.defaultCurrency.trim().toUpperCase() || 'USD',
          activate: this.activate,
        }),
      );
      this.success.set(true);
      await this.ctx.afterCreate();
      await this.router.navigate(['/organizations/onboarding']);
    } catch (e) {
      const msg =
        e instanceof OrganizationsApiError
          ? e.code === 'slug_conflict' || e.status === 409
            ? `Conflicto de slug: ${e.message}`
            : e.message
          : 'No se pudo crear la organización';
      this.error.set(msg);
      queueMicrotask(() => this.errorBox?.nativeElement.focus());
    } finally {
      this.submitting.set(false);
    }
  }
}
