import { Component, ElementRef, OnInit, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';
import { OrganizationCatalogs } from '../models/organization.models';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

export function slugFromDisplayName(name: string): string {
  return (
    name
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 48) || 'org'
  );
}

@Component({
  selector: 'app-org-create-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page org-page--create" data-testid="org-create-page">
      <header class="org-page__header">
        <span class="org-page__eyebrow">{{ 'organizations.create.eyebrow' | t:lang() }}</span>
        <h1>{{ 'organizations.create.title' | t:lang() }}</h1>
        <p class="lede">{{ 'organizations.create.lede' | t:lang() }}</p>
      </header>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert" #errorBox tabindex="-1">{{ error() }}</div>
      }
      @if (success()) {
        <div class="org-alert org-alert--ok" role="status">
          {{ 'organizations.create.success' | t:lang() }}
        </div>
      }

      <div class="org-create-shell">
        <aside class="org-create-guide" aria-label="Proceso de creación">
          <div class="org-create-guide__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 20V8l8-4 8 4v12M8 20v-7h8v7M9 9h.01M15 9h.01" /></svg>
          </div>
          <span class="org-create-guide__kicker">{{ 'organizations.create.guideKicker' | t:lang() }}</span>
          <h2>{{ 'organizations.create.guideTitle' | t:lang() }}</h2>
          <p>{{ 'organizations.create.guideText' | t:lang() }}</p>
          <ol class="org-create-steps">
            <li class="is-current">
              <span>1</span><div><strong>{{ 'organizations.create.stepProfile' | t:lang() }}</strong><small>{{ 'organizations.create.stepProfileHint' | t:lang() }}</small></div>
            </li>
            <li>
              <span>2</span><div><strong>{{ 'organizations.create.stepPlan' | t:lang() }}</strong><small>{{ 'organizations.create.stepPlanHint' | t:lang() }}</small></div>
            </li>
            <li>
              <span>3</span><div><strong>{{ 'organizations.create.stepTeam' | t:lang() }}</strong><small>{{ 'organizations.create.stepTeamHint' | t:lang() }}</small></div>
            </li>
          </ol>
          <div class="org-owner-note">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 5 6v5c0 4.7 2.9 8 7 10 4.1-2 7-5.3 7-10V6l-7-3Zm-3 9 2 2 4-5" /></svg>
            <span>{{ 'organizations.create.ownerNote' | t:lang() }}</span>
          </div>
        </aside>

        <form class="org-card org-form org-form--create" [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <div class="org-form-heading">
            <span>{{ 'organizations.create.formStep' | t:lang() }}</span>
            <h2>{{ 'organizations.create.primaryData' | t:lang() }}</h2>
            <p>{{ 'organizations.create.primaryDataHint' | t:lang() }}</p>
          </div>

          <div class="org-field-grid">
            <label>
              {{ 'organizations.create.name' | t:lang() }} *
              <input formControlName="display_name" required maxlength="200" autocomplete="organization" />
            </label>
            <label>
              {{ 'organizations.create.legalName' | t:lang() }}
              <input formControlName="legal_name" maxlength="200" autocomplete="organization" />
            </label>
          </div>

          <fieldset class="org-type-fieldset">
            <legend>{{ 'organizations.create.type' | t:lang() }} *</legend>
            <div class="org-type-picker">
              @for (opt of catalogs()?.organization_types || []; track opt.code) {
                <label class="org-type-option" [class.is-selected]="form.controls.organization_type.value === opt.code">
                  <input type="radio" formControlName="organization_type" [value]="opt.code" />
                  <span class="org-type-option__icon" aria-hidden="true">{{ typeInitial(opt.code) }}</span>
                  <span><strong>{{ opt.label }}</strong><small>{{ typeHint(opt.code) }}</small></span>
                </label>
              }
            </div>
          </fieldset>

          <label class="org-country-field">
            {{ 'organizations.create.country' | t:lang() }}
            <select formControlName="country_code">
              <option value="">{{ 'organizations.create.countryPlaceholder' | t:lang() }}</option>
              @for (opt of catalogs()?.countries || []; track opt.code) {
                <option [value]="opt.code">{{ opt.label }}</option>
              }
            </select>
            <small>{{ 'organizations.create.countryHint' | t:lang() }}</small>
          </label>

          <label class="org-check org-check--activate">
            <input type="checkbox" formControlName="activate" />
            <span><strong>{{ 'organizations.create.activate' | t:lang() }}</strong><small>{{ 'organizations.create.activateHint' | t:lang() }}</small></span>
          </label>

          <details class="org-advanced" [open]="advancedOpen()" data-testid="org-advanced">
            <summary (click)="toggleAdvanced($event)">{{ 'organizations.create.advanced' | t:lang() }}</summary>
            <div class="org-advanced-grid">
              <label>
                {{ 'organizations.create.slugLabel' | t:lang() }}
                <input #slugInput formControlName="slug" maxlength="48" data-testid="org-slug-input" (input)="markSlugEdited()" />
              </label>
              <label>
                {{ 'organizations.create.timezone' | t:lang() }}
                <select formControlName="timezone">
                  <option value="">{{ 'organizations.create.automatic' | t:lang() }}</option>
                  @for (opt of catalogs()?.timezones || []; track opt.code) { <option [value]="opt.code">{{ opt.label }}</option> }
                </select>
              </label>
              <label>
                {{ 'organizations.create.currency' | t:lang() }}
                <select formControlName="default_currency">
                  <option value="">{{ 'organizations.create.automatic' | t:lang() }}</option>
                  @for (opt of catalogs()?.currencies || []; track opt.code) { <option [value]="opt.code">{{ opt.label }}</option> }
                </select>
              </label>
            </div>
            <p class="org-muted">{{ 'organizations.create.slugHelp' | t:lang() }}</p>
          </details>

          <div class="org-actions org-actions--create">
            <a class="org-btn org-btn--ghost" routerLink="/business">{{ 'organizations.create.cancel' | t:lang() }}</a>
            <button class="org-btn" type="submit" [disabled]="form.invalid || submitting() || success()">
              {{ submitting() ? ('organizations.create.submitting' | t:lang()) : ('organizations.create.continue' | t:lang()) }}
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </form>
      </div>
    </section>
  `,
})
export class OrgCreatePageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  private readonly ctx = inject(OrganizationContextService);
  private readonly spaces = inject(SpaceContextService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  @ViewChild('errorBox') errorBox?: ElementRef<HTMLElement>;
  @ViewChild('slugInput') slugInput?: ElementRef<HTMLInputElement>;

  readonly catalogs = signal<OrganizationCatalogs | null>(null);

  readonly form = this.fb.nonNullable.group({
    display_name: ['', [Validators.required, Validators.maxLength(200)]],
    legal_name: [''],
    slug: [''],
    organization_type: ['label', Validators.required],
    country_code: [''],
    timezone: [''],
    default_currency: [''],
    activate: [true],
  });

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);
  readonly advancedOpen = signal(false);

  private slugEdited = false;
  private clientIntentId = `org-create-${crypto.randomUUID?.() || Date.now()}`;

  constructor() {
    this.form.controls.display_name.valueChanges.subscribe((name) => {
      if (this.slugEdited) return;
      this.form.controls.slug.setValue(slugFromDisplayName(name), { emitEvent: false });
    });
  }

  async ngOnInit(): Promise<void> {
    try {
      this.catalogs.set(await firstValueFrom(this.api.catalogs()));
    } catch {
      this.catalogs.set({
        organization_types: [
          { code: 'label', label: 'Sello' },
          { code: 'distributor', label: 'Distribuidor' },
          { code: 'publisher', label: 'Editora' },
          { code: 'management', label: 'Management' },
          { code: 'other', label: 'Otra' },
        ],
        countries: [
          { code: 'EC', label: 'Ecuador' },
          { code: 'AR', label: 'Argentina' },
          { code: 'BO', label: 'Bolivia' },
          { code: 'BR', label: 'Brasil' },
          { code: 'CL', label: 'Chile' },
          { code: 'CO', label: 'Colombia' },
          { code: 'CR', label: 'Costa Rica' },
          { code: 'DO', label: 'República Dominicana' },
          { code: 'SV', label: 'El Salvador' },
          { code: 'GT', label: 'Guatemala' },
          { code: 'HN', label: 'Honduras' },
          { code: 'MX', label: 'México' },
          { code: 'NI', label: 'Nicaragua' },
          { code: 'PA', label: 'Panamá' },
          { code: 'PY', label: 'Paraguay' },
          { code: 'PE', label: 'Perú' },
          { code: 'PR', label: 'Puerto Rico' },
          { code: 'UY', label: 'Uruguay' },
          { code: 'VE', label: 'Venezuela' },
          { code: 'CA', label: 'Canadá' },
          { code: 'US', label: 'Estados Unidos' },
          { code: 'ES', label: 'España' },
          { code: 'PT', label: 'Portugal' },
          { code: 'GB', label: 'Reino Unido' },
          { code: 'FR', label: 'Francia' },
          { code: 'DE', label: 'Alemania' },
          { code: 'IT', label: 'Italia' },
          { code: 'NL', label: 'Países Bajos' },
          { code: 'BE', label: 'Bélgica' },
          { code: 'CH', label: 'Suiza' },
          { code: 'IE', label: 'Irlanda' },
          { code: 'AU', label: 'Australia' },
          { code: 'NZ', label: 'Nueva Zelanda' },
          { code: 'JP', label: 'Japón' },
          { code: 'KR', label: 'Corea del Sur' },
          { code: 'IN', label: 'India' },
        ],
        timezones: [{ code: 'UTC', label: 'UTC' }],
        currencies: [{ code: 'USD', label: 'USD' }],
      });
    }
  }

  markSlugEdited(): void {
    this.slugEdited = true;
  }

  typeInitial(code: string): string {
    return ({ label: 'S', distributor: 'D', publisher: 'E', management: 'M', other: '+' } as Record<string, string>)[code] || '+';
  }

  typeHint(code: string): string {
    const key = `organizations.create.typeHint.${code}`;
    const translated = this.i18n.t(key);
    return translated === key ? this.i18n.t('organizations.create.typeHint.other') : translated;
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
      const created = await firstValueFrom(
        this.api.create({
          display_name: value.display_name.trim(),
          legal_name: value.legal_name.trim() || undefined,
          slug: value.slug.trim() ? value.slug.trim().toLowerCase() : undefined,
          organization_type: value.organization_type,
          country_code: value.country_code.trim().toUpperCase() || undefined,
          timezone: value.timezone.trim() || undefined,
          default_currency: value.default_currency.trim().toUpperCase() || undefined,
          activate: value.activate,
          client_intent_id: this.clientIntentId,
        }),
      );
      this.success.set(true);
      const orgId = created.organization.id;
      await this.ctx.afterCreate();
      try {
        await this.spaces.bootstrapFromSession();
        await this.spaces.selectSpace(`org:${orgId}`, { navigate: false });
      } catch {
        /* space refresh is best-effort; onboarding + productSurfaceGuard retry */
      }
      await this.router.navigate(['/organizations/onboarding'], {
        queryParams: { organization_id: orgId },
      });    } catch (e) {
      const slugConflict =
        e instanceof OrganizationsApiError &&
        (e.code === 'create_conflict' || e.code === 'slug_taken' || e.status === 409);
      const msg = slugConflict
        ? this.i18n.t('organizations.create.slugConflict', {
            message: (e as OrganizationsApiError).message,
          })
        : e instanceof OrganizationsApiError
          ? e.message
          : this.i18n.t('organizations.create.error');
      this.error.set(msg);
      if (slugConflict) {
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
