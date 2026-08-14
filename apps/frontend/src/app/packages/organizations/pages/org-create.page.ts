import { Component, ElementRef, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

export const ORG_TYPE_CATALOG = [
  { value: 'label', label: 'Sello' },
  { value: 'distributor', label: 'Distribuidor' },
  { value: 'publisher', label: 'Editora' },
  { value: 'management', label: 'Management' },
  { value: 'other', label: 'Otra' },
] as const;

export const ORG_COUNTRY_CATALOG = [
  { value: 'EC', label: 'Ecuador' },
  { value: 'MX', label: 'México' },
  { value: 'CO', label: 'Colombia' },
  { value: 'PE', label: 'Perú' },
  { value: 'CL', label: 'Chile' },
  { value: 'AR', label: 'Argentina' },
  { value: 'ES', label: 'España' },
  { value: 'US', label: 'Estados Unidos' },
] as const;

export const ORG_TIMEZONE_CATALOG = [
  { value: 'America/Guayaquil', label: 'America/Guayaquil' },
  { value: 'America/Bogota', label: 'America/Bogota' },
  { value: 'America/Mexico_City', label: 'America/Mexico_City' },
  { value: 'America/Lima', label: 'America/Lima' },
  { value: 'America/Santiago', label: 'America/Santiago' },
  { value: 'America/Argentina/Buenos_Aires', label: 'America/Argentina/Buenos_Aires' },
  { value: 'Europe/Madrid', label: 'Europe/Madrid' },
  { value: 'UTC', label: 'UTC' },
] as const;

export const ORG_CURRENCY_CATALOG = [
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'MXN', label: 'MXN' },
  { value: 'COP', label: 'COP' },
  { value: 'PEN', label: 'PEN' },
  { value: 'CLP', label: 'CLP' },
  { value: 'ARS', label: 'ARS' },
] as const;

export function slugFromDisplayName(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48) || 'org';
}

@Component({
  selector: 'app-org-create-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-create-page">
      <h1>{{ 'organizations.create.title' | t:lang() }}</h1>
      <p class="lede">{{ 'organizations.create.lede' | t:lang() }}</p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert" #errorBox tabindex="-1">{{ error() }}</div>
      }
      @if (success()) {
        <div class="org-alert org-alert--ok" role="status">
          {{ 'organizations.create.success' | t:lang() }}
        </div>
      }

      <form class="org-card org-form" [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <label>
          {{ 'organizations.create.name' | t:lang() }} *
          <input formControlName="display_name" required maxlength="200" />
        </label>
        <label>
          {{ 'organizations.create.legalName' | t:lang() }}
          <input formControlName="legal_name" maxlength="200" />
        </label>
        <p class="org-muted" data-testid="org-generated-slug">
          {{ 'organizations.create.identifier' | t:lang() }}: {{ form.controls.slug.value }}
        </p>
        <label>
          {{ 'organizations.create.type' | t:lang() }} *
          <select formControlName="organization_type">
            @for (opt of types; track opt.value) {
              <option [value]="opt.value">{{ opt.label }}</option>
            }
          </select>
        </label>
        <label>
          {{ 'organizations.create.country' | t:lang() }}
          <select formControlName="country_code">
            <option value="">—</option>
            @for (opt of countries; track opt.value) {
              <option [value]="opt.value">{{ opt.label }}</option>
            }
          </select>
        </label>
        <label>
          {{ 'organizations.create.timezone' | t:lang() }} *
          <select formControlName="timezone">
            @for (opt of timezones; track opt.value) {
              <option [value]="opt.value">{{ opt.label }}</option>
            }
          </select>
        </label>
        <label>
          {{ 'organizations.create.currency' | t:lang() }} *
          <select formControlName="default_currency">
            @for (opt of currencies; track opt.value) {
              <option [value]="opt.value">{{ opt.label }}</option>
            }
          </select>
        </label>
        <label>
          <input type="checkbox" formControlName="activate" />
          {{ 'organizations.create.activate' | t:lang() }}
        </label>

        <details class="org-advanced" [open]="advancedOpen()" data-testid="org-advanced">
          <summary (click)="toggleAdvanced($event)">
            {{ 'organizations.create.advanced' | t:lang() }}
          </summary>
          <label>
            {{ 'organizations.create.slugLabel' | t:lang() }}
            <input
              #slugInput
              formControlName="slug"
              maxlength="48"
              data-testid="org-slug-input"
              (input)="markSlugEdited()"
            />
          </label>
          <p class="org-muted">{{ 'organizations.create.slugHelp' | t:lang() }}</p>
        </details>

        <div class="org-actions">
          <button class="org-btn" type="submit" [disabled]="form.invalid || submitting() || success()">
            {{ submitting() ? ('organizations.create.submitting' | t:lang()) : ('organizations.create.title' | t:lang()) }}
          </button>
          <a class="org-btn org-btn--ghost" routerLink="/business">
            {{ 'organizations.create.cancel' | t:lang() }}
          </a>
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
  private readonly fb = inject(FormBuilder);

  @ViewChild('errorBox') errorBox?: ElementRef<HTMLElement>;
  @ViewChild('slugInput') slugInput?: ElementRef<HTMLInputElement>;

  readonly types = ORG_TYPE_CATALOG;
  readonly countries = ORG_COUNTRY_CATALOG;
  readonly timezones = ORG_TIMEZONE_CATALOG;
  readonly currencies = ORG_CURRENCY_CATALOG;

  readonly form = this.fb.nonNullable.group({
    display_name: ['', [Validators.required, Validators.maxLength(200)]],
    legal_name: [''],
    slug: ['org', Validators.required],
    organization_type: ['label', Validators.required],
    country_code: [''],
    timezone: ['America/Guayaquil', Validators.required],
    default_currency: ['USD', Validators.required],
    activate: [true],
  });

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);
  readonly advancedOpen = signal(false);

  /** Once the user edits the slug we stop deriving it from the display name. */
  private slugEdited = false;

  constructor() {
    this.form.controls.display_name.valueChanges.subscribe((name) => {
      if (this.slugEdited) return;
      this.form.controls.slug.setValue(slugFromDisplayName(name), { emitEvent: false });
    });
  }

  markSlugEdited(): void {
    this.slugEdited = true;
  }

  toggleAdvanced(event: Event): void {
    event.preventDefault();
    this.advancedOpen.update((open) => !open);
  }

  async submit(): Promise<void> {
    if (this.submitting() || this.success() || this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    const value = this.form.getRawValue();
    try {
      await firstValueFrom(
        this.api.create({
          display_name: value.display_name.trim(),
          legal_name: value.legal_name.trim() || undefined,
          slug: value.slug.trim().toLowerCase(),
          organization_type: value.organization_type,
          country_code: value.country_code.trim().toUpperCase() || undefined,
          timezone: value.timezone.trim() || 'UTC',
          default_currency: value.default_currency.trim().toUpperCase() || 'USD',
          activate: value.activate,
        }),
      );
      this.success.set(true);
      await this.ctx.afterCreate();
      await this.router.navigate(['/organizations/onboarding']);
    } catch (e) {
      const slugConflict =
        e instanceof OrganizationsApiError && (e.code === 'slug_conflict' || e.status === 409);
      const msg = slugConflict
        ? this.i18n.t('organizations.create.slugConflict', {
            message: (e as OrganizationsApiError).message,
          })
        : e instanceof OrganizationsApiError
          ? e.message
          : this.i18n.t('organizations.create.error');
      this.error.set(msg);
      if (slugConflict) {
        // Form values are preserved (reactive form); surface the field that must change.
        this.advancedOpen.set(true);
      }
      queueMicrotask(() => {
        if (slugConflict && this.slugInput) {
          this.slugInput.nativeElement.focus();
          this.slugInput.nativeElement.select();
          return;
        }
        this.errorBox?.nativeElement.focus();
      });
    } finally {
      this.submitting.set(false);
    }
  }
}
