import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-space-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.profile.title' | t:lang()"
        [subtitle]="'artistSpace.profile.subtitle' | t:lang()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="2" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <app-enterprise-section-card [title]="'artistSpace.profile.edit' | t:lang()">
          <form [formGroup]="form" (ngSubmit)="save()" class="form-grid">
            <app-enterprise-form-field
              [label]="'artistSpace.profile.displayName' | t:lang()"
              [required]="true"
            >
              <input class="input" formControlName="display_name" [readonly]="!canEdit()" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'artistSpace.profile.legalName' | t:lang()">
              <input class="input" formControlName="legal_name" [readonly]="!canEdit()" />
            </app-enterprise-form-field>
            @if (canEdit()) {
              <button type="submit" class="btn btn--primary" [disabled]="form.invalid || saving()">
                {{ 'common.save' | t:lang() }}
              </button>
            }
          </form>
          @if (saved()) {
            <p class="muted">{{ 'artistSpace.profile.saved' | t:lang() }}</p>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class ArtistSpaceProfilePage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly saving = signal(false);
  readonly saved = signal(false);

  readonly form = this.fb.nonNullable.group({
    display_name: ['', Validators.required],
    legal_name: [''],
  });

  canEdit(): boolean {
    return this.artistCtx.can('artist_space.profile.update');
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.loading.set(true);
    this.api.profile(id).subscribe({
      next: (p) => {
        this.form.patchValue({
          display_name: String(p['display_name'] ?? ''),
          legal_name: String(p['legal_name'] ?? ''),
        });
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.message || 'load_failed');
        this.loading.set(false);
      },
    });
  }

  save(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canEdit()) return;
    this.saving.set(true);
    this.saved.set(false);
    const v = this.form.getRawValue();
    this.api
      .patchProfile(id, {
        display_name: v.display_name,
        legal_name: v.legal_name || null,
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.saved.set(true);
        },
        error: (e) => {
          this.error.set(e?.message || 'save_failed');
          this.saving.set(false);
        },
      });
  }
}
