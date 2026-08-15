import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Observable, firstValueFrom } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { ArtistsApiService } from '../../artists/services/artists-api.service';
import { ArtistProfile } from '../../artists/models/artist.models';
import { ArtistContextService } from '../../artist-space/services/artist-context.service';
import { ArtistSpaceApiService } from '../../artist-space/services/artist-space-api.service';
import {
  ContributorCreateBody,
  MetadataUpdateBody,
  ReleaseSubmission,
  TrackCreateBody,
} from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

const STEPS = ['info', 'tracks', 'media', 'contributors', 'rights', 'review'] as const;
type StepId = (typeof STEPS)[number];

export type ReleaseWizardContext = 'organization' | 'artist';

/**
 * Context adapter: Artist Space posts to artist-scoped routes (tenant resolved
 * server-side), Organization Catalog posts to org routes with an explicit artist.
 */
interface PublishingGateway {
  createDraft(artistProfileId: number, title: string, meta: MetadataUpdateBody):
    Observable<ReleaseSubmission>;
  updateDraft(submissionId: number, meta: MetadataUpdateBody): Observable<ReleaseSubmission>;
  addTrack(submissionId: number, body: TrackCreateBody): Observable<Record<string, unknown>>;
  updateTrack(
    submissionId: number,
    trackId: number,
    body: Partial<TrackCreateBody>,
  ): Observable<Record<string, unknown>>;
  uploadAudio(
    submissionId: number,
    trackId: number,
    file: File,
  ): Observable<Record<string, unknown>>;
  uploadCover(submissionId: number, file: File): Observable<Record<string, unknown>>;
  addContributor(
    submissionId: number,
    body: ContributorCreateBody,
  ): Observable<Record<string, unknown>>;
  submit(submissionId: number): Observable<ReleaseSubmission>;
  detailRoute(submissionId: number): unknown[];
}

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
      @if (contextError()) {
        <app-enterprise-page-header
          [title]="'publishing.wizard.title' | t: lang()"
          [subtitle]="'publishing.wizard.subtitle' | t: lang()"
        />
        <app-enterprise-error-state [message]="contextError()!" (retry)="initContext()" />
      } @else if (context === 'organization' && !orgId()) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'publishing.wizard.title' | t: lang()"
          [subtitle]="'publishing.wizard.subtitle' | t: lang()"
          [badge]="contextBadge()"
        />

        <nav class="stepper" aria-label="wizard">
          @for (s of steps; track s; let i = $index) {
            <button
              type="button"
              class="step"
              [class.step--active]="step() === s"
              [class.step--done]="stepIndex() > i"
              (click)="goStep(s)"
            >
              <span class="step__n">{{ i + 1 }}</span>
              {{ stepLabel(s) }}
            </button>
          }
        </nav>

        @if (showPrivateBanner()) {
          <div class="private-banner" role="status">
            {{ 'publishing.media.privateBanner' | t: lang() }}
          </div>
        }

        <form [formGroup]="form" class="wizard-form" (ngSubmit)="onSubmit()">
          @if (step() === 'info') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.info' | t: lang()">
              @if (context === 'organization') {
                <app-enterprise-form-field
                  [label]="'publishing.field.artist' | t: lang()"
                  [required]="true"
                  [hint]="'publishing.wizard.artistRequiredHint' | t: lang()"
                >
                  <select
                    class="input"
                    formControlName="artist_profile_id"
                    data-testid="artist-select"
                  >
                    <option [ngValue]="null">
                      {{ 'publishing.wizard.selectArtist' | t: lang() }}
                    </option>
                    @for (a of orgArtists(); track a.id) {
                      <option [ngValue]="a.id">{{ a.display_name }}</option>
                    }
                  </select>
                </app-enterprise-form-field>
              } @else {
                <p class="fixed-artist" data-testid="fixed-artist">
                  {{ 'publishing.wizard.artistFixed' | t: lang() }}:
                  <strong>{{ activeArtistName() }}</strong>
                </p>
              }

              <div class="form-grid">
                <app-enterprise-form-field
                  [label]="'publishing.field.title' | t: lang()"
                  [required]="true"
                >
                  <input formControlName="title" class="input" data-testid="release-title" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.releaseType' | t: lang()">
                  <select formControlName="release_type" class="input">
                    <option value="single">Single</option>
                    <option value="ep">EP</option>
                    <option value="album">Album</option>
                  </select>
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.genre' | t: lang()">
                  <input formControlName="genre" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.language' | t: lang()">
                  <input formControlName="language" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.label' | t: lang()">
                  <input formControlName="label_name" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'publishing.field.plannedDate' | t: lang()">
                  <input formControlName="planned_release_date" type="date" class="input" />
                </app-enterprise-form-field>
              </div>
              <label class="check">
                <input type="checkbox" formControlName="explicit" />
                {{ 'publishing.field.explicit' | t: lang() }}
              </label>
            </app-enterprise-section-card>
          }

          @if (step() === 'tracks') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.tracks' | t: lang()">
              <div formArrayName="tracks">
                @for (group of tracks.controls; track $index; let i = $index) {
                  <div class="track-row" [formGroupName]="i">
                    <app-enterprise-form-field
                      [label]="'publishing.field.trackTitle' | t: lang()"
                      [required]="true"
                    >
                      <input formControlName="title" class="input" />
                    </app-enterprise-form-field>
                    <app-enterprise-form-field
                      [label]="'publishing.field.trackNumber' | t: lang()"
                    >
                      <input
                        formControlName="track_number"
                        type="number"
                        min="1"
                        class="input"
                      />
                    </app-enterprise-form-field>
                    <app-enterprise-form-field [label]="'publishing.field.isrc' | t: lang()">
                      <input formControlName="isrc" class="input" />
                    </app-enterprise-form-field>
                    @if (tracks.length > 1) {
                      <button type="button" class="btn btn--secondary" (click)="removeTrack(i)">
                        {{ 'common.remove' | t: lang() }}
                      </button>
                    }
                  </div>
                }
              </div>
              <button
                type="button"
                class="btn btn--secondary"
                data-testid="add-track"
                (click)="addTrack()"
              >
                {{ 'publishing.wizard.addTrack' | t: lang() }}
              </button>
              <p class="muted">{{ 'publishing.wizard.tracksHint' | t: lang() }}</p>
            </app-enterprise-section-card>
          }

          @if (step() === 'media') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.media' | t: lang()">
              @for (group of tracks.controls; track $index; let i = $index) {
                <app-enterprise-form-field
                  [label]="trackAudioLabel(i)"
                  [hint]="audioFileName(i)"
                >
                  <input
                    type="file"
                    accept="audio/*"
                    class="input"
                    (change)="onAudioSelected(i, $event)"
                  />
                </app-enterprise-form-field>
              }
              <app-enterprise-form-field
                [label]="'publishing.field.cover' | t: lang()"
                [hint]="coverFileName()"
              >
                <input
                  type="file"
                  accept="image/*"
                  class="input"
                  (change)="onCoverSelected($event)"
                />
              </app-enterprise-form-field>
              <p class="muted">{{ 'publishing.media.privateHint' | t: lang() }}</p>
            </app-enterprise-section-card>
          }

          @if (step() === 'contributors') {
            <app-enterprise-section-card
              [title]="'publishing.wizard.step.contributors' | t: lang()"
            >
              <div formArrayName="contributors">
                @for (group of contributors.controls; track $index; let i = $index) {
                  <div class="track-row" [formGroupName]="i">
                    <app-enterprise-form-field
                      [label]="'publishing.field.contributorName' | t: lang()"
                    >
                      <input formControlName="display_name" class="input" />
                    </app-enterprise-form-field>
                    <app-enterprise-form-field
                      [label]="'publishing.field.contributorRole' | t: lang()"
                    >
                      <select formControlName="party_role" class="input">
                        <option value="primary_artist">primary_artist</option>
                        <option value="featured">featured</option>
                        <option value="producer">producer</option>
                        <option value="songwriter">songwriter</option>
                      </select>
                    </app-enterprise-form-field>
                    <button type="button" class="btn btn--secondary" (click)="removeContributor(i)">
                      {{ 'common.remove' | t: lang() }}
                    </button>
                  </div>
                }
              </div>
              <button type="button" class="btn btn--secondary" (click)="addContributor()">
                {{ 'publishing.wizard.addContributor' | t: lang() }}
              </button>
            </app-enterprise-section-card>
          }

          @if (step() === 'rights') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.rights' | t: lang()">
              <app-enterprise-form-field [label]="'publishing.field.rightsContract' | t: lang()">
                <input formControlName="rights_contract_id" type="number" class="input" />
              </app-enterprise-form-field>
              <p class="muted">{{ 'publishing.wizard.rightsHint' | t: lang() }}</p>
            </app-enterprise-section-card>
          }

          @if (step() === 'review') {
            <app-enterprise-section-card [title]="'publishing.wizard.step.review' | t: lang()">
              <dl class="meta">
                <dt>{{ 'publishing.field.artist' | t: lang() }}</dt>
                <dd>{{ selectedArtistName() }}</dd>
                <dt>{{ 'publishing.field.title' | t: lang() }}</dt>
                <dd>{{ form.value.title }}</dd>
                <dt>{{ 'publishing.field.releaseType' | t: lang() }}</dt>
                <dd>{{ form.value.release_type }}</dd>
                <dt>{{ 'publishing.wizard.trackCount' | t: lang() }}</dt>
                <dd>{{ tracks.length }}</dd>
              </dl>
              @if (canSubmitRelease()) {
                <label class="check">
                  <input type="checkbox" formControlName="submit_now" data-testid="submit-now" />
                  {{ 'publishing.wizard.submitNow' | t: lang() }}
                </label>
              } @else {
                <p class="muted" data-testid="submit-forbidden">
                  {{ 'publishing.wizard.submitForbidden' | t: lang() }}
                </p>
              }
              @if (draftId()) {
                <p class="muted" data-testid="draft-id">
                  {{ 'publishing.wizard.draftSaved' | t: lang() }} #{{ draftId() }}
                </p>
              }
            </app-enterprise-section-card>
          }

          <div class="wizard-actions">
            <button
              type="button"
              class="btn btn--secondary"
              [disabled]="stepIndex() === 0"
              (click)="prev()"
            >
              {{ 'publishing.wizard.prev' | t: lang() }}
            </button>
            @if (step() !== 'review') {
              <button type="button" class="btn btn--primary" (click)="next()">
                {{ 'publishing.wizard.next' | t: lang() }}
              </button>
            } @else {
              <button
                type="submit"
                class="btn btn--primary"
                data-testid="wizard-save"
                [disabled]="busy() || form.invalid"
              >
                {{ submitLabel() }}
              </button>
            }
          </div>
        </form>

        @if (error()) {
          <app-enterprise-error-state
            [message]="error()!"
            [retryLabel]="'publishing.wizard.retry' | t: lang()"
            (retry)="onSubmit()"
          />
        }
        @if (info()) {
          <p class="success" role="status" data-testid="wizard-info">{{ info() }}</p>
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
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
    }
    .track-row {
      display: grid;
      gap: 0.75rem;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
      align-items: end;
      padding: 0.5rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .wizard-actions {
      display: flex;
      flex-wrap: wrap;
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
    .fixed-artist {
      margin: 0 0 0.85rem;
      font-size: 0.9rem;
    }
    .meta {
      display: grid;
      grid-template-columns: minmax(8rem, 12rem) 1fr;
      gap: 0.35rem 0.75rem;
    }
    .meta dd { margin: 0; }
    .muted { color: rgba(255, 255, 255, 0.55); font-size: 0.85rem; }
    .success { color: #6fd3a0; margin-top: 0.75rem; }
  `,
})
export class ArtistReleaseWizardPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(CatalogPublishingApiService);
  private readonly artistApi = inject(ArtistSpaceApiService);
  private readonly artistsApi = inject(ArtistsApiService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly i18n = inject(I18nService);
  private readonly access = catalogPublishingAccess();

  readonly lang = this.i18n.lang;
  readonly steps = STEPS;

  context: ReleaseWizardContext = 'organization';
  readonly step = signal<StepId>('info');
  readonly orgId = signal<number | null>(null);
  readonly orgArtists = signal<ArtistProfile[]>([]);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly contextError = signal<string | null>(null);
  readonly info = signal<string | null>(null);
  readonly draftId = signal<number | null>(null);

  /** Pending audio uploads keyed by the stable row uid (survives reordering). */
  private readonly audioFiles = new Map<number, File>();
  private coverFile: File | null = null;
  private coverUploaded = false;
  private nextTrackUid = 1;

  readonly form = this.fb.group({
    artist_profile_id: [null as number | null],
    title: ['', Validators.required],
    release_type: ['single'],
    genre: [''],
    language: [''],
    label_name: [''],
    planned_release_date: [''],
    explicit: [false],
    rights_contract_id: [null as number | null],
    submit_now: [false],
    tracks: this.fb.array<FormGroup>([this.trackGroup(1)]),
    contributors: this.fb.array<FormGroup>([]),
  });

  get tracks(): FormArray<FormGroup> {
    return this.form.controls.tracks;
  }

  get contributors(): FormArray<FormGroup> {
    return this.form.controls.contributors;
  }

  stepIndex(): number {
    return STEPS.indexOf(this.step());
  }

  ngOnInit(): void {
    this.context =
      (this.route.snapshot.data['releaseContext'] as ReleaseWizardContext | undefined) ??
      'organization';
    this.initContext();
  }

  initContext(): void {
    this.contextError.set(null);
    if (this.context === 'artist') {
      this.initArtistContext();
      return;
    }
    this.initOrganizationContext();
  }

  showPrivateBanner(): boolean {
    return this.audioFiles.size > 0 || this.coverFile != null;
  }

  contextBadge(): string {
    return this.i18n.t(
      this.context === 'artist'
        ? 'publishing.wizard.contextArtist'
        : 'publishing.wizard.contextOrganization',
    );
  }

  activeArtistName(): string {
    return this.artistCtx.displayName() ?? '';
  }

  selectedArtistName(): string {
    if (this.context === 'artist') return this.activeArtistName();
    const id = this.form.controls.artist_profile_id.value;
    return (
      this.orgArtists().find((a) => a.id === id)?.display_name ??
      this.i18n.t('publishing.wizard.selectArtist')
    );
  }

  /** Collaborators may persist drafts; only owner/administrator may submit. */
  canSubmitRelease(): boolean {
    if (this.context === 'artist') {
      return this.artistCtx.can('artist_space.release.submit');
    }
    return this.access.canSubmit();
  }

  submitLabel(): string {
    const submitting = this.canSubmitRelease() && !!this.form.controls.submit_now.value;
    return this.i18n.t(
      submitting ? 'publishing.wizard.createAndSubmit' : 'publishing.wizard.saveDraft',
    );
  }

  stepLabel(s: StepId): string {
    return this.i18n.t(`publishing.wizard.step.${s}`);
  }

  goStep(s: StepId): void {
    this.step.set(s);
  }

  next(): void {
    const index = this.stepIndex();
    if (index < STEPS.length - 1) this.step.set(STEPS[index + 1]);
  }

  prev(): void {
    const index = this.stepIndex();
    if (index > 0) this.step.set(STEPS[index - 1]);
  }

  addTrack(): void {
    this.tracks.push(this.trackGroup(this.tracks.length + 1));
  }

  removeTrack(index: number): void {
    if (this.tracks.length <= 1) return;
    this.audioFiles.delete(this.trackUid(index));
    this.tracks.removeAt(index);
  }

  addContributor(): void {
    this.contributors.push(
      this.fb.group({
        persisted_id: [null as number | null],
        display_name: [''],
        party_role: ['primary_artist'],
      }),
    );
  }

  removeContributor(index: number): void {
    this.contributors.removeAt(index);
  }

  trackAudioLabel(index: number): string {
    const title = String(this.tracks.at(index)?.get('title')?.value ?? '').trim();
    const base = this.i18n.t('publishing.field.audio');
    return title ? `${base} — ${title}` : `${base} #${index + 1}`;
  }

  audioFileName(index: number): string | undefined {
    return this.audioFiles.get(this.trackUid(index))?.name;
  }

  coverFileName(): string | undefined {
    return this.coverFile?.name;
  }

  onAudioSelected(index: number, ev: Event): void {
    const uid = this.trackUid(index);
    const file = (ev.target as HTMLInputElement).files?.[0] ?? null;
    if (file) {
      this.audioFiles.set(uid, file);
    } else {
      this.audioFiles.delete(uid);
    }
  }

  private trackUid(index: number): number {
    return Number(this.tracks.at(index)?.get('uid')?.value ?? -1);
  }

  onCoverSelected(ev: Event): void {
    this.coverFile = (ev.target as HTMLInputElement).files?.[0] ?? null;
    this.coverUploaded = false;
  }

  onSubmit(): Promise<void> | void {
    if (this.busy() || this.form.invalid) return;
    const artistProfileId = this.resolveArtistProfileId();
    if (artistProfileId == null) {
      this.error.set(this.i18n.t('publishing.wizard.artistRequired'));
      this.step.set('info');
      return;
    }
    const gateway = this.buildGateway(artistProfileId);
    if (!gateway) return;
    return this.runPipeline(gateway, artistProfileId);
  }

  /**
   * Persist every part in order. Any failure stops the wizard with a message —
   * partial work stays saved as a draft so the retry resumes instead of duplicating.
   */
  private async runPipeline(
    gateway: PublishingGateway,
    artistProfileId: number,
  ): Promise<void> {
    this.busy.set(true);
    this.error.set(null);
    this.info.set(null);
    const v = this.form.getRawValue();
    const meta: MetadataUpdateBody = {
      release_type: v.release_type || 'single',
      genre: v.genre || null,
      language: v.language || null,
      label_name: v.label_name || null,
      planned_release_date: v.planned_release_date || null,
      explicit: !!v.explicit,
      rights_contract_id: v.rights_contract_id || null,
    };

    try {
      let submissionId = this.draftId();
      if (submissionId == null) {
        const draft = await firstValueFrom(
          gateway.createDraft(artistProfileId, v.title!, meta),
        );
        submissionId = draft.id;
        this.draftId.set(submissionId);
      } else {
        await firstValueFrom(
          gateway.updateDraft(submissionId, { ...meta, title: v.title! }),
        );
      }

      await this.persistTracks(gateway, submissionId);
      await this.persistCover(gateway, submissionId);
      await this.persistContributors(gateway, submissionId);

      const shouldSubmit = this.canSubmitRelease() && !!v.submit_now;
      if (shouldSubmit) {
        await firstValueFrom(gateway.submit(submissionId));
        this.info.set(this.i18n.t('publishing.wizard.submitted'));
      } else {
        this.info.set(this.i18n.t('publishing.wizard.draftSaved'));
      }
      this.busy.set(false);
    } catch (e) {
      this.busy.set(false);
      this.error.set(userFacingHttpError(this.i18n, e));
      return;
    }

    // Navigation is best-effort after a durable save; never convert a saved draft into a false failure.
    const submissionId = this.draftId();
    if (submissionId != null) {
      try {
        await this.router.navigate(gateway.detailRoute(submissionId));
      } catch {
        /* stay on the wizard with the success banner */
      }
    }
  }

  private async persistTracks(
    gateway: PublishingGateway,
    submissionId: number,
  ): Promise<void> {
    const rows = this.tracks.controls;
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i];
      const value = row.getRawValue() as {
        uid: number;
        persisted_id: number | null;
        title: string;
        track_number: number;
        isrc: string;
      };
      const title = (value.title || '').trim() || (this.form.controls.title.value ?? '');
      const body: TrackCreateBody = {
        title,
        track_number: Number(value.track_number) || i + 1,
        isrc: value.isrc || null,
      };
      let trackId = value.persisted_id;
      if (trackId == null) {
        const created = await firstValueFrom(gateway.addTrack(submissionId, body));
        const rawId = created?.['id'];
        if (typeof rawId !== 'number') {
          throw new Error(this.i18n.t('publishing.wizard.trackIdMissing'));
        }
        trackId = rawId;
        row.get('persisted_id')?.setValue(trackId, { emitEvent: false });
      } else {
        // Retry / edit path: keep server track metadata in sync with the form.
        await firstValueFrom(gateway.updateTrack(submissionId, trackId, body));
      }
      const audio = this.audioFiles.get(value.uid);
      if (audio) {
        await firstValueFrom(gateway.uploadAudio(submissionId, trackId, audio));
        this.audioFiles.delete(value.uid);
      }
    }
  }

  private async persistCover(
    gateway: PublishingGateway,
    submissionId: number,
  ): Promise<void> {
    if (!this.coverFile || this.coverUploaded) return;
    await firstValueFrom(gateway.uploadCover(submissionId, this.coverFile));
    this.coverUploaded = true;
  }

  private async persistContributors(
    gateway: PublishingGateway,
    submissionId: number,
  ): Promise<void> {
    for (const control of this.contributors.controls) {
      const value = control.getRawValue() as {
        persisted_id: number | null;
        display_name: string;
        party_role: string;
      };
      const displayName = (value.display_name || '').trim();
      if (!displayName) continue;
      if (value.persisted_id != null) continue;
      const created = await firstValueFrom(
        gateway.addContributor(submissionId, {
          display_name: displayName,
          party_role: value.party_role || 'primary_artist',
          track_id: null,
        }),
      );
      const rawId = created?.['id'];
      if (typeof rawId !== 'number') {
        throw new Error(this.i18n.t('publishing.wizard.contributorIdMissing'));
      }
      control.get('persisted_id')?.setValue(rawId, { emitEvent: false });
    }
  }

  /** No first-profile fallback: the artist is fixed by context or chosen explicitly. */
  private resolveArtistProfileId(): number | null {
    if (this.context === 'artist') {
      return this.artistCtx.artistProfileId();
    }
    return this.form.controls.artist_profile_id.value ?? null;
  }

  private buildGateway(artistProfileId: number): PublishingGateway | null {
    if (this.context === 'artist') {
      const artistApi = this.artistApi;
      return {
        createDraft: (profileId, title, meta) =>
          artistApi.createArtistRelease(profileId, {
            title,
            release_type: meta.release_type,
            genre: meta.genre,
            language: meta.language,
            label_name: meta.label_name,
            planned_release_date: meta.planned_release_date,
            explicit: meta.explicit,
            rights_contract_id: meta.rights_contract_id,
          }),
        updateDraft: (submissionId, meta) =>
          artistApi.updateArtistRelease(artistProfileId, submissionId, meta),
        addTrack: (submissionId, body) =>
          artistApi.addArtistTrack(artistProfileId, submissionId, body),
        updateTrack: (submissionId, trackId, body) =>
          artistApi.updateArtistTrack(artistProfileId, submissionId, trackId, body),
        uploadAudio: (submissionId, trackId, file) =>
          artistApi.uploadArtistTrackAudio(artistProfileId, submissionId, trackId, file),
        uploadCover: (submissionId, file) =>
          artistApi.uploadArtistCover(artistProfileId, submissionId, file),
        addContributor: (submissionId, body) =>
          artistApi.addArtistContributor(artistProfileId, submissionId, body),
        submit: (submissionId) =>
          artistApi.submitArtistRelease(artistProfileId, submissionId),
        // Artist Space has one music surface; the saved draft is listed there.
        detailRoute: () => ['/artist-space/music'],
      };
    }

    const orgId = this.orgId();
    if (orgId == null) {
      this.error.set(this.i18n.t('publishing.wizard.orgRequired'));
      return null;
    }
    const api = this.api;
    const isDemo = this.access.isArtistPortalDemo();
    return {
      createDraft: (profileId, title, meta) =>
        api.createDraft(orgId, {
          artist_profile_id: profileId,
          title,
          release_type: meta.release_type,
          genre: meta.genre,
          language: meta.language,
          label_name: meta.label_name,
          planned_release_date: meta.planned_release_date,
          explicit: meta.explicit,
          rights_contract_id: meta.rights_contract_id,
          is_demo: isDemo,
        }),
      updateDraft: (submissionId, meta) => api.updateRelease(orgId, submissionId, meta),
      addTrack: (submissionId, body) => api.addTrack(orgId, submissionId, body),
      updateTrack: (submissionId, trackId, body) =>
        api.updateTrack(orgId, submissionId, trackId, body),
      uploadAudio: (submissionId, trackId, file) =>
        api.uploadAudio(orgId, submissionId, trackId, file),
      uploadCover: (submissionId, file) => api.uploadCover(orgId, submissionId, file),
      addContributor: (submissionId, body) => api.addContributor(orgId, submissionId, body),
      submit: (submissionId) => api.submitRelease(orgId, submissionId),
      detailRoute: (submissionId) => ['/artist/releases', submissionId],
    };
  }

  private initArtistContext(): void {
    if (this.artistCtx.artistProfileId() == null) {
      this.contextError.set(this.i18n.t('artistSpace.error.noActiveArtist'));
      return;
    }
    if (!this.artistCtx.can('artist_space.release.create')) {
      this.contextError.set(this.i18n.t('publishing.wizard.forbidden'));
      return;
    }
    this.form.controls.artist_profile_id.clearValidators();
    this.form.controls.artist_profile_id.updateValueAndValidity({ emitEvent: false });
  }

  private initOrganizationContext(): void {
    const orgId = this.orgCtx.organizationId();
    this.orgId.set(orgId);
    if (orgId == null) return;
    if (!this.access.canCreate()) {
      this.contextError.set(this.i18n.t('publishing.wizard.forbidden'));
      return;
    }
    this.form.controls.artist_profile_id.addValidators(Validators.required);
    this.form.controls.artist_profile_id.updateValueAndValidity({ emitEvent: false });
    this.artistsApi.list(orgId, { status: 'active', page_size: 100 }).subscribe({
      next: (page) => this.orgArtists.set(page?.items ?? []),
      error: (e) => this.contextError.set(userFacingHttpError(this.i18n, e)),
    });
  }

  private trackGroup(trackNumber: number): FormGroup {
    return this.fb.group({
      uid: [this.nextTrackUid++],
      persisted_id: [null as number | null],
      title: ['', Validators.required],
      track_number: [trackNumber],
      isrc: [''],
    });
  }
}
