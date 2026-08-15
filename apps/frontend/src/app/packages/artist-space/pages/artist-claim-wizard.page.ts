import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { artistJourneyError } from '../services/artist-space-error';
import {
  ARTIST_ASSIGNABLE_ROLES,
  ARTIST_RELATIONSHIP_TYPES,
  ArtistAccessRequest,
  ArtistAccessRequestCreateBody,
  ArtistDiscoveryItem,
  artistDiscoveryActionLabelKey,
  artistManagementStateLabelKey,
  artistRelationshipLabelKey,
  artistRequestStatusLabelKey,
  artistRequestTypeLabelKey,
  artistRoleLabelKey,
  isHttpUrl,
} from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { SpaceContextService } from '../../../core/spaces/space-context.service';

type WizardMode = 'choice' | 'discover' | 'create';
type PendingForm = 'claim' | 'access' | null;

/** Optional-but-validated absolute URL (evidence links are user supplied). */
function optionalHttpUrl(control: AbstractControl): ValidationErrors | null {
  const raw = typeof control.value === 'string' ? control.value.trim() : '';
  if (!raw) return null;
  return isHttpUrl(raw) ? null : { url: true };
}

@Component({
  selector: 'app-artist-claim-wizard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise artist-claim-wizard-page">
      <app-enterprise-page-header
        [title]="'artistSpace.claim.title' | t: lang()"
        [subtitle]="'artistSpace.claim.subtitle' | t: lang()"
      />

      @if (mode() === 'choice') {
        <app-enterprise-section-card [title]="'artistSpace.claim.chooseTitle' | t: lang()">
          <p class="hint">{{ 'artistSpace.claim.chooseHint' | t: lang() }}</p>
          <ul class="choice-grid">
            <li>
              <button
                type="button"
                class="choice-card"
                data-testid="choice-discover"
                (click)="openDiscover()"
              >
                <span class="choice-card__title">
                  {{ 'artistSpace.claim.choice.discoverTitle' | t: lang() }}
                </span>
                <span class="choice-card__body">
                  {{ 'artistSpace.claim.choice.discoverBody' | t: lang() }}
                </span>
              </button>
            </li>
            <li>
              <button
                type="button"
                class="choice-card"
                data-testid="choice-create"
                (click)="openCreate()"
              >
                <span class="choice-card__title">
                  {{ 'artistSpace.claim.choice.createTitle' | t: lang() }}
                </span>
                <span class="choice-card__body">
                  {{ 'artistSpace.claim.choice.createBody' | t: lang() }}
                </span>
              </button>
            </li>
            <li>
              <a
                class="choice-card"
                routerLink="/artist-invitations/accept"
                data-testid="choice-invitation"
              >
                <span class="choice-card__title">
                  {{ 'artistSpace.claim.choice.invitationTitle' | t: lang() }}
                </span>
                <span class="choice-card__body">
                  {{ 'artistSpace.claim.choice.invitationBody' | t: lang() }}
                </span>
              </a>
            </li>
          </ul>
        </app-enterprise-section-card>
      }

      @if (mode() === 'discover') {
        <app-enterprise-section-card [title]="'artistSpace.claim.search' | t: lang()">
          <button type="button" class="btn btn--secondary btn--back" (click)="backToChoice()">
            {{ 'artistSpace.claim.back' | t: lang() }}
          </button>
          <form [formGroup]="searchForm" (ngSubmit)="search()" class="search-form">
            <app-enterprise-form-field
              [label]="'artistSpace.claim.query' | t: lang()"
              [required]="true"
              [hint]="'artistSpace.claim.queryHint' | t: lang()"
            >
              <input class="input" formControlName="q" data-testid="discover-query" />
            </app-enterprise-form-field>
            <button
              type="submit"
              class="btn btn--primary"
              [disabled]="searchForm.invalid || searching()"
            >
              {{ 'common.search' | t: lang() }}
            </button>
          </form>

          @if (searching()) {
            <app-enterprise-loading-skeleton [rows]="3" />
          } @else if (searchError()) {
            <app-enterprise-error-state [message]="searchError()!" (retry)="search()" />
          } @else if (searched() && !results().length) {
            <div data-testid="discover-empty">
              <app-enterprise-empty-state
                [title]="'artistSpace.claim.noResultsTitle' | t: lang()"
                [description]="'artistSpace.claim.noResultsBody' | t: lang()"
                [ctaLabel]="'artistSpace.claim.createNew' | t: lang()"
                (ctaClick)="focusCreateNew()"
              />
            </div>
          } @else if (results().length) {
            <ul class="results" data-testid="discover-results">
              @for (a of results(); track a.warehouse_artist_id) {
                <li class="result">
                  <div class="result__main">
                    <strong class="result__name">{{ a.display_name }}</strong>
                    <span class="chip chip--{{ a.management_state }}">
                      {{ stateLabelKey(a) | t: lang() }}
                    </span>
                  </div>
                  <div class="result__actions">
                    @if (a.allowed_action === 'none') {
                      <span class="muted">
                        {{ 'artistSpace.discovery.action.none' | t: lang() }}
                      </span>
                    } @else {
                      <button
                        type="button"
                        class="btn btn--primary"
                        [attr.data-action]="a.allowed_action"
                        (click)="runAllowedAction(a)"
                      >
                        {{ actionLabelKey(a) | t: lang() }}
                      </button>
                    }
                  </div>
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>

        @if (pendingForm() === 'claim' && selected(); as candidate) {
          <app-enterprise-section-card
            [title]="'artistSpace.claim.evidenceTitle' | t: lang()"
            [subtitle]="candidate.display_name"
          >
            <p class="hint">{{ 'artistSpace.claim.evidenceHint' | t: lang() }}</p>
            <form [formGroup]="claimForm" (ngSubmit)="submitClaim()" class="form-grid">
              <app-enterprise-form-field
                [label]="'artistSpace.claim.relationship' | t: lang()"
                [required]="true"
              >
                <select class="input" formControlName="relationship_type">
                  @for (rel of relationships; track rel) {
                    <option [value]="rel">{{ relationshipLabelKey(rel) | t: lang() }}</option>
                  }
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field
                [label]="'artistSpace.claim.evidenceUrl' | t: lang()"
                [error]="claimUrlError()"
              >
                <input
                  class="input"
                  formControlName="evidence_url"
                  inputmode="url"
                  placeholder="https://"
                />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'artistSpace.claim.evidenceNote' | t: lang()">
                <textarea class="input textarea" rows="3" formControlName="evidence_note"></textarea>
              </app-enterprise-form-field>
              <div class="form-actions">
                <button type="button" class="btn btn--secondary" (click)="cancelPendingForm()">
                  {{ 'common.cancel' | t: lang() }}
                </button>
                <button
                  type="submit"
                  class="btn btn--primary"
                  [disabled]="claimForm.invalid || submitting()"
                >
                  {{ 'artistSpace.claim.submitClaim' | t: lang() }}
                </button>
              </div>
            </form>
            @if (!hasClaimEvidence()) {
              <p class="warn">{{ 'artistSpace.claim.evidenceRequired' | t: lang() }}</p>
            }
          </app-enterprise-section-card>
        }

        @if (pendingForm() === 'access' && selected(); as candidate) {
          <app-enterprise-section-card
            [title]="'artistSpace.claim.accessTitle' | t: lang()"
            [subtitle]="candidate.display_name"
          >
            <p class="hint">{{ 'artistSpace.claim.requestAccessHint' | t: lang() }}</p>
            <form [formGroup]="accessForm" (ngSubmit)="submitAccess()" class="form-grid">
              <app-enterprise-form-field
                [label]="'artistSpace.team.role' | t: lang()"
                [required]="true"
              >
                <select class="input" formControlName="proposed_role">
                  @for (role of assignableRoles; track role) {
                    <option [value]="role">{{ roleLabelKey(role) | t: lang() }}</option>
                  }
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'artistSpace.claim.relationship' | t: lang()">
                <select class="input" formControlName="relationship_type">
                  <option value="">{{ 'common.optional' | t: lang() }}</option>
                  @for (rel of relationships; track rel) {
                    <option [value]="rel">{{ relationshipLabelKey(rel) | t: lang() }}</option>
                  }
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'artistSpace.claim.evidenceNote' | t: lang()">
                <textarea
                  class="input textarea"
                  rows="3"
                  formControlName="evidence_note"
                ></textarea>
              </app-enterprise-form-field>
              <div class="form-actions">
                <button type="button" class="btn btn--secondary" (click)="cancelPendingForm()">
                  {{ 'common.cancel' | t: lang() }}
                </button>
                <button
                  type="submit"
                  class="btn btn--primary"
                  [disabled]="accessForm.invalid || submitting()"
                >
                  {{ 'artistSpace.claim.submitAccess' | t: lang() }}
                </button>
              </div>
            </form>
          </app-enterprise-section-card>
        }
      }

      @if (mode() === 'create') {
        <app-enterprise-section-card [title]="'artistSpace.claim.createNew' | t: lang()">
          <button type="button" class="btn btn--secondary btn--back" (click)="backToChoice()">
            {{ 'artistSpace.claim.back' | t: lang() }}
          </button>
          <p class="hint" id="artist-claim-create">
            {{ 'artistSpace.claim.createHint' | t: lang() }}
          </p>
          <form [formGroup]="createForm" (ngSubmit)="createNew()" class="form-grid">
            <app-enterprise-form-field
              [label]="'artistSpace.claim.proposedName' | t: lang()"
              [required]="true"
            >
              <input class="input" formControlName="name" data-testid="create-name" />
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'artistSpace.claim.relationship' | t: lang()"
              [required]="true"
            >
              <select class="input" formControlName="relationship_type">
                @for (rel of relationships; track rel) {
                  <option [value]="rel">{{ relationshipLabelKey(rel) | t: lang() }}</option>
                }
              </select>
            </app-enterprise-form-field>
            <label class="check">
              <input type="checkbox" formControlName="accuracy_attested" />
              {{ 'artistSpace.claim.attestation' | t: lang() }}
            </label>
            <div class="form-actions">
              <button
                type="submit"
                class="btn btn--primary"
                [disabled]="createForm.invalid || submitting()"
              >
                {{ 'artistSpace.claim.submitCreate' | t: lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>
      }

      @if (message()) {
        <p class="ok" role="status" data-testid="claim-message">{{ message() }}</p>
      }
      @if (error()) {
        <app-enterprise-error-state [message]="error()!" />
      }

      <app-enterprise-section-card [title]="'artistSpace.claim.myRequests' | t: lang()">
        @if (requestsError()) {
          <app-enterprise-error-state [message]="requestsError()!" (retry)="reloadMine()" />
        } @else if (!mine().length) {
          <p class="muted">{{ 'artistSpace.claim.noRequests' | t: lang() }}</p>
        } @else {
          <ul class="requests" id="artist-claim-requests">
            @for (r of mine(); track r.id) {
              <li class="request-card">
                <div class="request-card__head">
                  <strong>{{ requestTypeLabelKey(r) | t: lang() }}</strong>
                  <app-enterprise-status-badge
                    [status]="badgeStatus(r.status)"
                    [label]="requestStatusLabelKey(r) | t: lang()"
                  />
                </div>
                <p class="request-card__body">{{ requestSubject(r) }}</p>
                @if (r.rejection_reason) {
                  <p class="request-card__reason">
                    {{ 'artistSpace.request.rejectionReason' | t: lang() }}:
                    {{ r.rejection_reason }}
                  </p>
                }
                @if (r.status === 'pending') {
                  <button type="button" class="btn btn--secondary" (click)="cancel(r.id)">
                    {{ 'artistSpace.request.cancel' | t: lang() }}
                  </button>
                }
              </li>
            }
          </ul>
        }
      </app-enterprise-section-card>
    </div>
  `,
  styles: [
    `
      .artist-claim-wizard-page {
        --claim-border: var(--vx-border, rgba(255, 255, 255, 0.12));
        --claim-muted: var(--vx-text-secondary, rgba(255, 255, 255, 0.6));
      }
      .hint {
        margin: 0 0 1rem;
        color: var(--claim-muted);
        font-size: 0.9rem;
        line-height: 1.45;
      }
      .muted {
        color: var(--claim-muted);
        font-size: 0.9rem;
      }
      .warn {
        color: var(--vx-warning, #f0c36a);
        font-size: 0.85rem;
        margin: 0.5rem 0 0;
      }
      .choice-grid {
        display: grid;
        gap: 0.85rem;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .choice-card {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        width: 100%;
        height: 100%;
        text-align: left;
        text-decoration: none;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid var(--claim-border);
        background: rgba(255, 255, 255, 0.03);
        color: inherit;
        cursor: pointer;
      }
      .choice-card:hover,
      .choice-card:focus-visible {
        border-color: var(--vx-accent, #6fd3a0);
      }
      .choice-card__title {
        font-weight: 600;
      }
      .choice-card__body {
        font-size: 0.85rem;
        color: var(--claim-muted);
        line-height: 1.4;
      }
      .btn--back {
        margin-bottom: 1rem;
      }
      .search-form {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-end;
        gap: 0.75rem;
        margin-bottom: 1rem;
      }
      .search-form app-enterprise-form-field {
        flex: 1 1 16rem;
        min-width: 0;
      }
      .form-grid {
        display: grid;
        gap: 0.85rem;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
      }
      .form-grid .form-actions,
      .form-grid .check {
        grid-column: 1 / -1;
      }
      .form-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      .check {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        font-size: 0.9rem;
        line-height: 1.4;
      }
      .textarea {
        width: 100%;
        resize: vertical;
      }
      .results,
      .requests {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .result {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--claim-border);
      }
      .result__main {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.5rem;
        min-width: 0;
      }
      .result__name {
        overflow-wrap: anywhere;
      }
      .chip {
        border-radius: 999px;
        padding: 0.15rem 0.6rem;
        font-size: 0.72rem;
        border: 1px solid var(--claim-border);
        color: var(--claim-muted);
        white-space: nowrap;
      }
      .chip--unmanaged {
        border-color: rgba(111, 211, 160, 0.4);
        color: #6fd3a0;
      }
      .chip--pending {
        border-color: rgba(240, 195, 106, 0.4);
        color: #f0c36a;
      }
      .request-card {
        padding: 0.85rem 0;
        border-bottom: 1px solid var(--claim-border);
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        align-items: flex-start;
      }
      .request-card__head {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.6rem;
      }
      .request-card__body,
      .request-card__reason {
        margin: 0;
        font-size: 0.88rem;
        color: var(--claim-muted);
      }
      .ok {
        color: var(--vx-success, #6fd3a0);
      }
      @media (max-width: 640px) {
        .result {
          align-items: flex-start;
          flex-direction: column;
        }
        .result__actions .btn {
          width: 100%;
        }
      }
    `,
  ],
})
export class ArtistClaimWizardPage {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);
  private readonly spaces = inject(SpaceContextService);
  private readonly router = inject(Router);

  readonly lang = this.i18n.lang;
  readonly relationships = ARTIST_RELATIONSHIP_TYPES;
  readonly assignableRoles = ARTIST_ASSIGNABLE_ROLES;

  readonly mode = signal<WizardMode>('choice');
  readonly pendingForm = signal<PendingForm>(null);
  readonly selected = signal<ArtistDiscoveryItem | null>(null);
  readonly results = signal<ArtistDiscoveryItem[]>([]);
  readonly searched = signal(false);
  readonly searching = signal(false);
  readonly submitting = signal(false);
  readonly mine = signal<ArtistAccessRequest[]>([]);
  readonly message = signal<string | null>(null);
  readonly error = signal<string | null>(null);
  readonly searchError = signal<string | null>(null);
  readonly requestsError = signal<string | null>(null);

  readonly searchForm = this.fb.nonNullable.group({
    q: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
  });

  readonly claimForm = this.fb.nonNullable.group({
    relationship_type: ['artist_self', Validators.required],
    evidence_url: ['', optionalHttpUrl],
    evidence_note: [''],
  });

  readonly accessForm = this.fb.nonNullable.group({
    proposed_role: ['member', Validators.required],
    relationship_type: [''],
    evidence_note: [''],
  });

  readonly createForm = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(200)]],
    relationship_type: ['artist_self', Validators.required],
    accuracy_attested: [false, Validators.requiredTrue],
  });

  constructor() {
    this.reloadMine();
  }

  /** Backend requires a URL or a note before a claim is reviewable. */
  hasClaimEvidence(): boolean {
    const v = this.claimForm.getRawValue();
    return !!(v.evidence_url.trim() || v.evidence_note.trim());
  }

  stateLabelKey(item: ArtistDiscoveryItem): string {
    return artistManagementStateLabelKey(item.management_state);
  }

  actionLabelKey(item: ArtistDiscoveryItem): string {
    return artistDiscoveryActionLabelKey(item.allowed_action);
  }

  relationshipLabelKey(relationship: string): string {
    return artistRelationshipLabelKey(relationship);
  }

  roleLabelKey(role: string): string {
    return artistRoleLabelKey(role);
  }

  requestTypeLabelKey(request: ArtistAccessRequest): string {
    return artistRequestTypeLabelKey(request.request_type);
  }

  requestStatusLabelKey(request: ArtistAccessRequest): string {
    return artistRequestStatusLabelKey(request.status);
  }

  badgeStatus(status: string): string {
    const normalized = (status || '').toLowerCase();
    if (normalized === 'approved') return 'published';
    if (normalized === 'rejected' || normalized === 'cancelled') return 'error';
    return 'pending';
  }

  requestSubject(request: ArtistAccessRequest): string {
    if (request.proposed_display_name) return request.proposed_display_name;
    if (request.warehouse_artist_id != null) {
      return `${this.i18n.t('artistSpace.request.catalogArtist')} #${request.warehouse_artist_id}`;
    }
    if (request.target_artist_profile_id != null) {
      return `${this.i18n.t('artistSpace.request.artistProfile')} #${request.target_artist_profile_id}`;
    }
    return this.i18n.t('artistSpace.request.unknownSubject');
  }

  claimUrlError(): string | undefined {
    const control = this.claimForm.controls.evidence_url;
    if (!control.touched || !control.hasError('url')) return undefined;
    return this.i18n.t('artistSpace.claim.invalidUrl');
  }

  openDiscover(): void {
    this.resetFeedback();
    this.mode.set('discover');
  }

  openCreate(): void {
    this.resetFeedback();
    this.mode.set('create');
  }

  backToChoice(): void {
    this.resetFeedback();
    this.pendingForm.set(null);
    this.selected.set(null);
    this.mode.set('choice');
  }

  cancelPendingForm(): void {
    this.pendingForm.set(null);
    this.selected.set(null);
  }

  search(): void {
    const q = this.searchForm.getRawValue().q.trim();
    if (!q) return;
    this.searching.set(true);
    this.searchError.set(null);
    this.api.discoverArtists(q).subscribe({
      next: (response) => {
        this.results.set(response?.items ?? []);
        this.searched.set(true);
        this.searching.set(false);
      },
      error: (e) => {
        this.results.set([]);
        this.searchError.set(artistJourneyError(this.i18n, e));
        this.searching.set(false);
      },
    });
  }

  focusCreateNew(): void {
    const name = this.searchForm.getRawValue().q.trim();
    if (name) {
      this.createForm.patchValue({ name });
    }
    this.mode.set('create');
  }

  /** The server decides the single action; the client only executes it. */
  runAllowedAction(item: ArtistDiscoveryItem): void {
    this.resetFeedback();
    this.selected.set(item);
    switch (item.allowed_action) {
      case 'claim_ownership':
        this.pendingForm.set('claim');
        return;
      case 'request_access':
        this.pendingForm.set('access');
        return;
      case 'open_space':
        this.pendingForm.set(null);
        void this.openArtistSpace();
        return;
      case 'view_request':
        this.pendingForm.set(null);
        document
          .getElementById('artist-claim-requests')
          ?.scrollIntoView({ behavior: 'smooth' });
        return;
      case 'none':
        this.pendingForm.set(null);
        return;
      default: {
        const exhaustive: never = item.allowed_action;
        this.error.set(String(exhaustive));
      }
    }
  }

  submitClaim(): void {
    const candidate = this.selected();
    if (!candidate || this.claimForm.invalid) return;
    if (!this.hasClaimEvidence()) {
      this.error.set(this.i18n.t('artistSpace.claim.evidenceRequired'));
      return;
    }
    const v = this.claimForm.getRawValue();
    this.submit({
      request_type: 'claim_ownership',
      warehouse_artist_id: candidate.warehouse_artist_id,
      relationship_type: v.relationship_type as ArtistAccessRequestCreateBody['relationship_type'],
      evidence_url: v.evidence_url.trim() || null,
      evidence_note: v.evidence_note.trim() || null,
      accuracy_attested: true,
    });
  }

  submitAccess(): void {
    const candidate = this.selected();
    if (!candidate || this.accessForm.invalid) return;
    const v = this.accessForm.getRawValue();
    this.submit({
      request_type: 'request_access',
      warehouse_artist_id: candidate.warehouse_artist_id,
      target_artist_profile_id: candidate.artist_profile_id,
      proposed_role: v.proposed_role,
      relationship_type:
        (v.relationship_type as ArtistAccessRequestCreateBody['relationship_type']) || null,
      evidence_note: v.evidence_note.trim() || null,
    });
  }

  createNew(): void {
    if (this.createForm.invalid) return;
    const v = this.createForm.getRawValue();
    this.submit({
      request_type: 'create_new',
      proposed_display_name: v.name.trim(),
      relationship_type: v.relationship_type as ArtistAccessRequestCreateBody['relationship_type'],
      accuracy_attested: v.accuracy_attested,
    });
  }

  cancel(id: number): void {
    this.error.set(null);
    this.api.cancelAccessRequest(id).subscribe({
      next: () => {
        this.message.set(this.i18n.t('artistSpace.request.cancelled'));
        this.reloadMine();
      },
      error: (e) => this.error.set(artistJourneyError(this.i18n, e)),
    });
  }

  reloadMine(): void {
    this.requestsError.set(null);
    this.api.listMyAccessRequests().subscribe({
      next: (rows) => this.mine.set(rows ?? []),
      error: (e) => this.requestsError.set(artistJourneyError(this.i18n, e)),
    });
  }

  private submit(body: ArtistAccessRequestCreateBody): void {
    this.resetFeedback();
    this.submitting.set(true);
    this.api.createAccessRequest(body).subscribe({
      next: () => {
        this.submitting.set(false);
        this.message.set(this.i18n.t('artistSpace.claim.submitted'));
        this.pendingForm.set(null);
        this.selected.set(null);
        this.reloadMine();
        if (this.searched()) {
          this.search();
        }
        // Approval may already have granted a space; refresh without logout.
        void this.spaces.bootstrap({ force: true });
      },
      error: (e) => {
        this.submitting.set(false);
        this.error.set(artistJourneyError(this.i18n, e));
      },
    });
  }

  private async openArtistSpace(): Promise<void> {
    await this.spaces.bootstrap({ force: true });
    await this.router.navigateByUrl('/artist-space');
  }

  private resetFeedback(): void {
    this.error.set(null);
    this.message.set(null);
  }
}
