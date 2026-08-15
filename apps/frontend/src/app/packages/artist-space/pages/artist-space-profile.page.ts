import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { artistJourneyError } from '../services/artist-space-error';
import {
  ArtistExternalIdentifier,
  ArtistProfileDetail,
  artistRoleLabelKey,
  isHttpUrl,
} from '../models/artist-space.models';
import {
  ARTIST_COUNTRY_CATALOG,
  ARTIST_GENRE_CATALOG,
  ARTIST_IDENTIFIER_SYSTEMS,
} from '../models/artist-catalogs';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

function optionalHttpUrl(control: AbstractControl): ValidationErrors | null {
  const raw = typeof control.value === 'string' ? control.value.trim() : '';
  if (!raw) return null;
  return isHttpUrl(raw) ? null : { url: true };
}

interface IdentifierGroupValue {
  system_code: string;
  external_value: string;
}

@Component({
  selector: 'app-artist-space-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-space-profile-page">
      <app-enterprise-page-header
        [title]="'artistSpace.profile.title' | t: lang()"
        [subtitle]="'artistSpace.profile.subtitle' | t: lang()"
        [badge]="roleBadge()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (loadError()) {
        <app-enterprise-error-state [message]="loadError()!" (retry)="load()" />
      } @else {
        <app-enterprise-section-card
          [title]="'artistSpace.profile.edit' | t: lang()"
          [subtitle]="canEdit() ? undefined : ('artistSpace.profile.readOnly' | t: lang())"
        >
          <form [formGroup]="form" (ngSubmit)="save()">
            <div class="form-grid">
              <app-enterprise-form-field
                [label]="'artistSpace.profile.displayName' | t: lang()"
                [required]="true"
              >
                <input
                  class="input"
                  formControlName="display_name"
                  data-testid="profile-display-name"
                />
              </app-enterprise-form-field>

              @if (showLegalName()) {
                <app-enterprise-form-field
                  [label]="'artistSpace.profile.legalName' | t: lang()"
                  [hint]="'artistSpace.profile.legalNameHint' | t: lang()"
                >
                  <input class="input" formControlName="legal_name" />
                </app-enterprise-form-field>
              }

              <app-enterprise-form-field [label]="'artistSpace.profile.country' | t: lang()">
                <select class="input" formControlName="country_code">
                  <option value="">{{ 'common.notSet' | t: lang() }}</option>
                  @for (opt of countries; track opt.value) {
                    <option [value]="opt.value">{{ opt.label }}</option>
                  }
                </select>
              </app-enterprise-form-field>

              <app-enterprise-form-field [label]="'artistSpace.profile.genre' | t: lang()">
                <select class="input" formControlName="primary_genre">
                  <option value="">{{ 'common.notSet' | t: lang() }}</option>
                  @for (opt of genres; track opt.value) {
                    <option [value]="opt.value">{{ opt.label }}</option>
                  }
                </select>
              </app-enterprise-form-field>

              <app-enterprise-form-field
                [label]="'artistSpace.profile.website' | t: lang()"
                [error]="urlError('website_url')"
              >
                <input class="input" formControlName="website_url" placeholder="https://" />
              </app-enterprise-form-field>

              <app-enterprise-form-field
                [label]="'artistSpace.profile.imageUrl' | t: lang()"
                [error]="urlError('image_url')"
              >
                <input class="input" formControlName="image_url" placeholder="https://" />
              </app-enterprise-form-field>
            </div>

            <app-enterprise-form-field
              [label]="'artistSpace.profile.bio' | t: lang()"
              [hint]="bioHint()"
            >
              <textarea class="input textarea" rows="4" formControlName="bio"></textarea>
            </app-enterprise-form-field>

            <fieldset class="identifiers" formArrayName="external_identifiers">
              <legend>{{ 'artistSpace.profile.identifiers' | t: lang() }}</legend>
              <p class="hint">{{ 'artistSpace.profile.identifiersHint' | t: lang() }}</p>
              @if (!identifiers.length) {
                <p class="muted">{{ 'artistSpace.profile.noIdentifiers' | t: lang() }}</p>
              }
              @for (group of identifiers.controls; track $index; let i = $index) {
                <div class="identifier-row" [formGroupName]="i">
                  <app-enterprise-form-field
                    [label]="'artistSpace.profile.identifierSystem' | t: lang()"
                  >
                    <select class="input" formControlName="system_code">
                      @for (sys of identifierSystems; track sys.value) {
                        <option [value]="sys.value">{{ sys.label }}</option>
                      }
                    </select>
                  </app-enterprise-form-field>
                  <app-enterprise-form-field
                    [label]="'artistSpace.profile.identifierValue' | t: lang()"
                  >
                    <input class="input" formControlName="external_value" />
                  </app-enterprise-form-field>
                  @if (canEdit()) {
                    <button
                      type="button"
                      class="btn btn--secondary"
                      (click)="removeIdentifier(i)"
                    >
                      {{ 'common.remove' | t: lang() }}
                    </button>
                  }
                </div>
              }
              @if (canEdit()) {
                <button
                  type="button"
                  class="btn btn--secondary"
                  data-testid="add-identifier"
                  (click)="addIdentifier()"
                >
                  {{ 'artistSpace.profile.addIdentifier' | t: lang() }}
                </button>
              }
            </fieldset>

            @if (canEdit()) {
              <div class="form-actions">
                <button
                  type="submit"
                  class="btn btn--primary"
                  data-testid="profile-save"
                  [disabled]="form.invalid || saving()"
                >
                  {{ saving() ? ('common.saving' | t: lang()) : ('common.save' | t: lang()) }}
                </button>
                <button
                  type="button"
                  class="btn btn--secondary"
                  [disabled]="saving()"
                  (click)="load()"
                >
                  {{ 'common.discardChanges' | t: lang() }}
                </button>
              </div>
            }
          </form>

          @if (saveError()) {
            <app-enterprise-error-state [message]="saveError()!" />
          }
          @if (saved()) {
            <p class="ok" role="status" data-testid="profile-saved">
              {{ 'artistSpace.profile.saved' | t: lang() }}
            </p>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
  styles: [
    `
      .artist-space-profile-page {
        --profile-border: var(--vx-border, rgba(255, 255, 255, 0.12));
        --profile-muted: var(--vx-text-secondary, rgba(255, 255, 255, 0.6));
      }
      .form-grid {
        display: grid;
        gap: 0.85rem;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        margin-bottom: 0.85rem;
      }
      .textarea {
        width: 100%;
        resize: vertical;
      }
      .identifiers {
        border: 1px solid var(--profile-border);
        border-radius: 10px;
        padding: 1rem;
        margin: 1.25rem 0 0;
      }
      .identifiers legend {
        padding: 0 0.4rem;
        font-size: 0.9rem;
        font-weight: 600;
      }
      .identifier-row {
        display: grid;
        gap: 0.75rem;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        align-items: end;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--profile-border);
      }
      .identifier-row:last-of-type {
        border-bottom: none;
      }
      .form-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1.25rem;
      }
      .hint,
      .muted {
        color: var(--profile-muted);
        font-size: 0.85rem;
        line-height: 1.45;
      }
      .hint {
        margin: 0 0 0.75rem;
      }
      .ok {
        color: var(--vx-success, #6fd3a0);
        margin-top: 0.75rem;
      }
    `,
  ],
})
export class ArtistSpaceProfilePage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);

  readonly lang = this.i18n.lang;
  readonly countries = ARTIST_COUNTRY_CATALOG;
  readonly genres = ARTIST_GENRE_CATALOG;
  readonly identifierSystems = ARTIST_IDENTIFIER_SYSTEMS;

  readonly loading = signal(true);
  readonly loadError = signal<string | null>(null);
  readonly saveError = signal<string | null>(null);
  readonly saving = signal(false);
  readonly saved = signal(false);
  readonly profile = signal<ArtistProfileDetail | null>(null);

  readonly form = this.fb.nonNullable.group({
    display_name: ['', [Validators.required, Validators.maxLength(200)]],
    legal_name: [''],
    bio: ['', Validators.maxLength(2000)],
    country_code: [''],
    primary_genre: [''],
    website_url: ['', optionalHttpUrl],
    image_url: ['', optionalHttpUrl],
    external_identifiers: this.fb.array<FormGroup>([]),
  });

  get identifiers(): FormArray<FormGroup> {
    return this.form.controls.external_identifiers;
  }

  canEdit(): boolean {
    return this.artistCtx.can('artist_space.profile.update');
  }

  /** Legal name is non-public: only roles allowed to edit the profile see it. */
  showLegalName(): boolean {
    return this.canEdit();
  }

  roleBadge(): string | undefined {
    const role = this.artistCtx.membershipRole();
    return role ? this.i18n.t(artistRoleLabelKey(role)) : undefined;
  }

  bioHint(): string {
    const used = (this.form.controls.bio.value || '').length;
    return `${used}/2000`;
  }

  urlError(field: 'website_url' | 'image_url'): string | undefined {
    const control = this.form.controls[field];
    if (!control.touched || !control.hasError('url')) return undefined;
    return this.i18n.t('artistSpace.profile.invalidUrl');
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) {
      this.loading.set(false);
      this.loadError.set(this.i18n.t('artistSpace.error.noActiveArtist'));
      return;
    }
    this.loading.set(true);
    this.loadError.set(null);
    this.saveError.set(null);
    this.saved.set(false);
    this.api.profile(id).subscribe({
      next: (p) => {
        this.profile.set(p);
        this.patchFromProfile(p);
        this.applyEditability();
        this.loading.set(false);
      },
      error: (e) => {
        this.loadError.set(artistJourneyError(this.i18n, e));
        this.loading.set(false);
      },
    });
  }

  addIdentifier(): void {
    if (!this.canEdit()) return;
    this.identifiers.push(this.identifierGroup({ system_code: 'spotify', external_value: '' }));
  }

  removeIdentifier(index: number): void {
    if (!this.canEdit()) return;
    this.identifiers.removeAt(index);
  }

  save(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canEdit() || this.form.invalid) return;
    this.saving.set(true);
    this.saved.set(false);
    this.saveError.set(null);

    const v = this.form.getRawValue();
    const identifiers = (v.external_identifiers as unknown as IdentifierGroupValue[])
      .map((row) => ({
        system_code: (row.system_code || '').trim(),
        external_value: (row.external_value || '').trim(),
      }))
      .filter((row) => row.system_code && row.external_value);

    this.api
      .patchProfile(id, {
        display_name: v.display_name.trim(),
        legal_name: v.legal_name.trim() || null,
        bio: v.bio.trim() || null,
        country_code: v.country_code || null,
        primary_genre: v.primary_genre || null,
        website_url: v.website_url.trim() || null,
        image_url: v.image_url.trim() || null,
        external_identifiers: identifiers,
      })
      .subscribe({
        next: (updated) => {
          this.saving.set(false);
          this.saved.set(true);
          this.profile.set(updated);
          this.patchFromProfile(updated);
        },
        error: (e) => {
          this.saving.set(false);
          this.saveError.set(artistJourneyError(this.i18n, e));
        },
      });
  }

  private patchFromProfile(p: ArtistProfileDetail): void {
    this.form.patchValue(
      {
        display_name: p.display_name ?? '',
        legal_name: p.legal_name ?? '',
        bio: p.bio ?? '',
        country_code: p.country_code ?? '',
        primary_genre: p.primary_genre ?? '',
        website_url: p.website_url ?? '',
        image_url: p.image_url ?? '',
      },
      { emitEvent: false },
    );
    this.identifiers.clear();
    for (const row of p.external_identifiers ?? []) {
      this.identifiers.push(this.identifierGroup(row));
    }
  }

  private identifierGroup(row: ArtistExternalIdentifier): FormGroup {
    return this.fb.nonNullable.group({
      system_code: [row.system_code, Validators.required],
      external_value: [row.external_value, Validators.maxLength(200)],
    });
  }

  private applyEditability(): void {
    if (this.canEdit()) {
      this.form.enable({ emitEvent: false });
    } else {
      this.form.disable({ emitEvent: false });
    }
  }
}
