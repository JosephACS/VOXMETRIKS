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
        <label>
          {{ 'organizations.create.type' | t:lang() }} *
          <select formControlName="organization_type">
            @for (opt of catalogs()?.organization_types || []; track opt.code) {
              <option [value]="opt.code">{{ opt.label }}</option>
            }
          </select>
        </label>
        <label>
          {{ 'organizations.create.country' | t:lang() }}
          <select formControlName="country_code">
            <option value="">—</option>
            @for (opt of catalogs()?.countries || []; track opt.code) {
              <option [value]="opt.code">{{ opt.label }}</option>
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
          <label>
            {{ 'organizations.create.timezone' | t:lang() }}
            <select formControlName="timezone">
              <option value="">Automático</option>
              @for (opt of catalogs()?.timezones || []; track opt.code) {
                <option [value]="opt.code">{{ opt.label }}</option>
              }
            </select>
          </label>
          <label>
            {{ 'organizations.create.currency' | t:lang() }}
            <select formControlName="default_currency">
              <option value="">Automático</option>
              @for (opt of catalogs()?.currencies || []; track opt.code) {
                <option [value]="opt.code">{{ opt.label }}</option>
              }
            </select>
          </label>
        </details>

        <div class="org-actions">
          <button class="org-btn" type="submit" [disabled]="form.invalid || submitting() || success()">
            {{
              submitting()
                ? ('organizations.create.submitting' | t:lang())
                : ('organizations.create.title' | t:lang())
            }}
          </button>
          <a class="org-btn org-btn--ghost" routerLink="/business">
            {{ 'organizations.create.cancel' | t:lang() }}
          </a>
        </div>
      </form>
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
          { code: 'MX', label: 'México' },
          { code: 'CO', label: 'Colombia' },
          { code: 'PE', label: 'Perú' },
          { code: 'CL', label: 'Chile' },
          { code: 'AR', label: 'Argentina' },
          { code: 'ES', label: 'España' },
          { code: 'US', label: 'Estados Unidos' },
        ],
        timezones: [{ code: 'UTC', label: 'UTC' }],
        currencies: [{ code: 'USD', label: 'USD' }],
      });
    }
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
