import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { catchError, forkJoin, map, of, switchMap } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { ReleaseSubmission } from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

const STEPS = ['info', 'tracks', 'media', 'contributors', 'rights', 'review'] as const;
type StepId = (typeof STEPS)[number];

@Component({
  selector: 'app-artist-release-wizard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise artist-release-wizard-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'publishing.wizard.title' | t:lang()"
          [subtitle]="'publishing.wizard.subtitle' | t:lang()"
        />

        <nav class="stepper" aria-label="wizard">
          @for (s of steps; track s; let i = $index) {
            <button
              type="button"
              class="step"
              [class.step--active]="step === s"
              [class.step--done]="stepIndex > i"
              (click)="goStep(s)"
            >
              <span class="step__n">{{ i + 1 }}</span>
              {{ stepLabel(s) }}
            </button>
          }
        </nav>

        @if (showPrivateBanner) {
          <div class="private-banner" role="status">
            {{ 'publishing.media.privateBanner' | t:lang() }}
          </div>
        }

        <form [formGroup]="form" class="wizard-form" (ngSubmit)="onSubmit()">
          @if (step === 'info') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.info' | t:lang()">
              <div class="form-grid">
                <app-enterprise-form-field [label]="'publishing.field.title' | t:lang()" [required]="true">
                  <input formControlName="title" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.releaseType' | t:lang()">
                  <select formControlName="release_type" class="input">
                    <option value="single">Single</option>
                    <option value="ep">EP</option>
                    <option value="album">Album</option>
                  </select>
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.genre' | t:lang()">
                  <input formControlName="genre" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.language' | t:lang()">
                  <input formControlName="language" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.label' | t:lang()">
                  <input formControlName="label_name" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.plannedDate' | t:lang()">
                  <input formControlName="planned_release_date" type="date" class="input" />
                </app-enterprise-form-field>
                <label class="check">
                  <input type="checkbox" formControlName="explicit" />
                  {{ 'publishing.field.explicit' | t:lang() }}
                </label>
              </div>
            </app-enterprise-section-card>
          }

          @if (step === 'tracks') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.tracks' | t:lang()">
              <div class="form-grid" formGroupName="track">
                <app-enterprise-form-field [label]="'publishing.field.trackTitle' | t:lang()" [required]="true">
                  <input formControlName="title" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.trackNumber' | t:lang()">
                  <input formControlName="track_number" type="number" min="1" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.isrc' | t:lang()">
                  <input formControlName="isrc" class="input" />
                </app-enterprise-form-field>
              </div>
              <p class="muted">{{ 'publishing.wizard.tracksHint' | t:lang() }}</p>
            </app-enterprise-section-card>
          }

          @if (step === 'media') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.media' | t:lang()">
              <app-enterprise-form-field [label]="'publishing.field.audio' | t:lang()">
                <input type="file" accept="audio/*" (change)="onAudioSelected($event)" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'publishing.field.cover' | t:lang()">
                <input type="file" accept="image/*" (change)="onCoverSelected($event)" class="input" />
              </app-enterprise-form-field>
              <p class="muted">{{ 'publishing.media.privateHint' | t:lang() }}</p>
            </app-enterprise-section-card>
          }

          @if (step === 'contributors') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.contributors' | t:lang()">
              <div class="form-grid" formGroupName="contributor">
                <app-enterprise-form-field [label]="'publishing.field.contributorName' | t:lang()">
                  <input formControlName="display_name" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.contributorRole' | t:lang()">
                  <select formControlName="party_role" class="input">
                    <option value="primary_artist">primary_artist</option>
                    <option value="featured">featured</option>
                    <option value="producer">producer</option>
                    <option value="songwriter">songwriter</option>
                  </select>
                </app-enterprise-form-field>
              </div>
            </app-enterprise-section-card>
          }

          @if (step === 'rights') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.rights' | t:lang()">
              <app-enterprise-form-field [label]="'publishing.field.rightsContract' | t:lang()">
                <input formControlName="rights_contract_id" type="number" class="input" />
              </app-enterprise-form-field>
              <p class="muted">{{ 'publishing.wizard.rightsHint' | t:lang() }}</p>
            </app-enterprise-section-card>
          }

          @if (step === 'review') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.review' | t:lang()">
              <dl class="meta">
                <dt>{{ 'publishing.field.title' | t:lang() }}</dt>
                <dd>{{ form.value.title }}</dd>
                <dt>{{ 'publishing.field.releaseType' | t:lang() }}</dt>
                <dd>{{ form.value.release_type }}</dd>
                <dt>{{ 'publishing.field.trackTitle' | t:lang() }}</dt>
                <dd>{{ form.value.track?.title || '—' }}</dd>
              </dl>
              <label class="check">
                <input type="checkbox" formControlName="submit_now" />
                {{ 'publishing.wizard.submitNow' | t:lang() }}
              </label>
            </app-enterprise-section-card>
          }

          <div class="wizard-actions">
            <button type="button" class="btn btn--secondary" [disabled]="stepIndex === 0" (click)="prev()">
              {{ 'publishing.wizard.prev' | t:lang() }}
            </button>
            @if (step !== 'review') {
              <button type="button" class="btn btn--primary" (click)="next()">
                {{ 'publishing.wizard.next' | t:lang() }}
              </button>
            } @else {
              <button type="submit" class="btn btn--primary" [disabled]="busy || form.invalid">
                {{ 'publishing.wizard.create' | t:lang() }}
              </button>
            }
          </div>
        </form>

        @if (error) {
          <app-enterprise-error-state [message]="error" />
        }
      }
    </div>
  `,
  styles: `
    .stepper {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 1.25rem;
    }
    .step {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(255, 255, 255, 0.03);
      color: rgba(255, 255, 255, 0.65);
      border-radius: 999px;
      padding: 0.35rem 0.7rem;
      font-size: 0.78rem;
      cursor: pointer;
    }
    .step--active { border-color: #6fd3a0; color: #fff; }
    .step--done { color: #6fd3a0; }
    .step__n {
      width: 1.25rem;
      height: 1.25rem;
      border-radius: 50%;
      display: inline-grid;
      place-items: center;
      background: rgba(255, 255, 255, 0.08);
      font-size: 0.7rem;
    }
    .form-grid {
      display: grid;
      gap: 0.85rem;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .wizard-actions {
      display: flex;
      justify-content: space-between;
      gap: 0.75rem;
      margin-top: 1rem;
    }
    .private-banner {
      margin: 0 0 1rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: rgba(240, 195, 106, 0.12);
      border: 1px solid rgba(240, 195, 106, 0.35);
      color: #f0c36a;
      font-size: 0.9rem;
    }
    .check {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-top: 0.5rem;
    }
    .meta {
      display: grid;
      grid-template-columns: minmax(8rem, 12rem) 1fr;
      gap: 0.35rem 0.75rem;
    }
    .meta dd { margin: 0; }
    .muted { color: rgba(255, 255, 255, 0.55); font-size: 0.85rem; }
  `,
})
export class ArtistReleaseWizardPage implements OnInit {
  private fb = inject(FormBuilder);
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private router = inject(Router);
  private i18n = inject(I18nService);
  private access = catalogPublishingAccess();
  readonly lang = this.i18n.lang;

  readonly steps = STEPS;
  step: StepId = 'info';
  orgId: number | null = null;
  artistProfileId: number | null = null;
  busy = false;
  error: string | null = null;
  showPrivateBanner = false;
  private audioFile: File | null = null;
  private coverFile: File | null = null;

  form = this.fb.group({
    title: ['', Validators.required],
    release_type: ['single'],
    genre: [''],
    language: [''],
    label_name: [''],
    planned_release_date: [''],
    explicit: [false],
    rights_contract_id: [null as number | null],
    submit_now: [false],
    track: this.fb.group({
      title: [''],
      track_number: [1],
      isrc: [''],
    }),
    contributor: this.fb.group({
      display_name: [''],
      party_role: ['primary_artist'],
    }),
  });

  get stepIndex(): number {
    return STEPS.indexOf(this.step);
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    if (!this.access.canCreate()) {
      this.error = this.i18n.t('publishing.wizard.forbidden');
      return;
    }
    this.api
      .portalSummary(this.orgId)
      .pipe(catchError(() => of(null)))
      .subscribe((s) => {
        this.artistProfileId = s?.artist_profile_ids?.[0] ?? null;
      });
  }

  stepLabel(s: StepId): string {
    return this.i18n.t(`publishing.wizard.step.${s}`);
  }

  goStep(s: StepId): void {
    this.step = s;
  }

  next(): void {
    if (this.stepIndex < STEPS.length - 1) {
      this.step = STEPS[this.stepIndex + 1];
    }
  }

  prev(): void {
    if (this.stepIndex > 0) {
      this.step = STEPS[this.stepIndex - 1];
    }
  }

  onAudioSelected(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    this.audioFile = input.files?.[0] ?? null;
    this.showPrivateBanner = !!this.audioFile;
  }

  onCoverSelected(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    this.coverFile = input.files?.[0] ?? null;
  }

  onSubmit(): void {
    if (!this.orgId || this.form.invalid || this.busy) return;
    if (!this.artistProfileId) {
      this.error = this.i18n.t('publishing.wizard.noArtistProfile');
      return;
    }
    this.busy = true;
    this.error = null;
    const v = this.form.getRawValue();
    const orgId = this.orgId;

    this.api
      .createDraft(orgId, {
        artist_profile_id: this.artistProfileId,
        title: v.title!,
        release_type: v.release_type || 'single',
        genre: v.genre || null,
        language: v.language || null,
        label_name: v.label_name || null,
        planned_release_date: v.planned_release_date || null,
        explicit: !!v.explicit,
        rights_contract_id: v.rights_contract_id || null,
        is_demo: this.access.isArtistPortalDemo(),
      })
      .pipe(
        switchMap((sub) => {
          const trackTitle = v.track?.title?.trim() || v.title!;
          return this.api
            .addTrack(orgId, sub.id, {
              title: trackTitle,
              track_number: Number(v.track?.track_number) || 1,
              isrc: v.track?.isrc || null,
            })
            .pipe(
              catchError(() => of(null)),
              switchMap((track) => {
                const trackId = track && typeof track['id'] === 'number' ? (track['id'] as number) : null;
                const ops = [];
                if (this.audioFile && trackId != null) {
                  ops.push(
                    this.api
                      .uploadAudio(orgId, sub.id, trackId, this.audioFile)
                      .pipe(catchError(() => of(null))),
                  );
                }
                if (this.coverFile) {
                  ops.push(
                    this.api
                      .uploadCover(orgId, sub.id, this.coverFile)
                      .pipe(catchError(() => of(null))),
                  );
                }
                const contribName = v.contributor?.display_name?.trim();
                if (contribName) {
                  ops.push(
                    this.api
                      .addContributor(orgId, sub.id, {
                        display_name: contribName,
                        party_role: v.contributor?.party_role || 'primary_artist',
                        track_id: trackId,
                      })
                      .pipe(catchError(() => of(null))),
                  );
                }
                const after = ops.length
                  ? forkJoin(ops).pipe(map(() => sub))
                  : of(sub);
                if (!v.submit_now) return after;
                return after.pipe(
                  switchMap((s) =>
                    this.api
                      .submitRelease(orgId, s.id)
                      .pipe(catchError(() => of(s))),
                  ),
                );
              }),
            );
        }),
      )
      .subscribe({
        next: (sub: ReleaseSubmission) => {
          this.busy = false;
          void this.router.navigate(['/artist/releases', sub.id]);
        },
        error: (e) => {
          this.error = userFacingHttpError(this.i18n, e);
          this.busy = false;
        },
      });
  }
}
