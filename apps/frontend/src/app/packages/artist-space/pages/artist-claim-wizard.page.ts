import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistAccessRequest } from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { SpaceContextService } from '../../../core/spaces/space-context.service';

@Component({
  selector: 'app-artist-claim-wizard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.claim.title' | t:lang()"
        [subtitle]="'artistSpace.claim.subtitle' | t:lang()"
      />

      <app-enterprise-section-card [title]="'artistSpace.claim.search' | t:lang()">
        <form [formGroup]="searchForm" (ngSubmit)="search()" class="form-grid">
          <app-enterprise-form-field [label]="'artistSpace.claim.query' | t:lang()" [required]="true">
            <input class="input" formControlName="q" />
          </app-enterprise-form-field>
          <button type="submit" class="btn btn--primary" [disabled]="searchForm.invalid">
            {{ 'common.search' | t:lang() }}
          </button>
        </form>
        @if (searched() && !results().length) {
          <app-enterprise-empty-state
            [title]="'artistSpace.claim.noResultsTitle' | t:lang()"
            [description]="'artistSpace.claim.noResultsBody' | t:lang()"
            [ctaLabel]="'artistSpace.claim.createNew' | t:lang()"
            (ctaClick)="focusCreateNew()"
          />
        } @else if (results().length) {
          <ul class="results">
            @for (a of results(); track a.id_artista) {
              <li>
                <strong>{{ a.nombre_artista }}</strong>
                <span class="muted">#{{ a.id_artista }}</span>
                <button type="button" class="btn btn--primary" (click)="claim(a.id_artista)">
                  {{ 'artistSpace.claim.claimOwnership' | t:lang() }}
                </button>
                <button type="button" class="btn btn--secondary" (click)="requestAccess(a)">
                  {{ 'artistSpace.claim.requestAccess' | t:lang() }}
                </button>
              </li>
            }
          </ul>
        }
      </app-enterprise-section-card>

      <app-enterprise-section-card [title]="'artistSpace.claim.createNew' | t:lang()">
        <p class="muted hint" id="artist-claim-create">
          {{ 'artistSpace.claim.requestAccessHint' | t:lang() }}
        </p>
        <form [formGroup]="createForm" (ngSubmit)="createNew()" class="form-grid">
          <app-enterprise-form-field
            [label]="'artistSpace.claim.proposedName' | t:lang()"
            [required]="true"
          >
            <input class="input" formControlName="name" />
          </app-enterprise-form-field>
          <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
            {{ 'artistSpace.claim.submitCreate' | t:lang() }}
          </button>
        </form>
      </app-enterprise-section-card>

      @if (message()) {
        <p class="ok">{{ message() }}</p>
      }
      @if (error()) {
        <p class="err">{{ error() }}</p>
      }

      <app-enterprise-section-card [title]="'artistSpace.claim.myRequests' | t:lang()">
        @if (mine().length === 0) {
          <p class="muted">{{ 'artistSpace.claim.noRequests' | t:lang() }}</p>
        } @else {
          <ul>
            @for (r of mine(); track r.id) {
              <li>
                #{{ r.id }} {{ r.request_type }} — {{ r.status }}
                @if (r.status === 'pending') {
                  <button type="button" class="btn btn--secondary" (click)="cancel(r.id)">
                    {{ 'common.cancel' | t:lang() }}
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
      .results {
        list-style: none;
        padding: 0;
      }
      .results li {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: center;
        padding: 0.5rem 0;
      }
      .ok {
        color: var(--vx-success, #2a7);
      }
      .err {
        color: var(--vx-danger, #c33);
      }
    `,
  ],
})
export class ArtistClaimWizardPage {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);
  private readonly spaces = inject(SpaceContextService);

  readonly lang = this.i18n.lang;
  readonly results = signal<Array<{ id_artista: number; nombre_artista: string }>>([]);
  readonly searched = signal(false);
  readonly mine = signal<ArtistAccessRequest[]>([]);
  readonly message = signal<string | null>(null);
  readonly error = signal<string | null>(null);

  readonly searchForm = this.fb.nonNullable.group({
    q: ['', Validators.required],
  });
  readonly createForm = this.fb.nonNullable.group({
    name: ['', Validators.required],
  });

  constructor() {
    this.reloadMine();
  }

  search(): void {
    const q = this.searchForm.value.q?.trim() || '';
    this.api.searchCatalogArtists(q).subscribe({
      next: (r) => {
        this.results.set(r.items || []);
        this.searched.set(true);
      },
      error: (e) => this.error.set(e?.message || 'search_failed'),
    });
  }

  focusCreateNew(): void {
    const name = this.searchForm.value.q?.trim() || '';
    if (name) {
      this.createForm.patchValue({ name });
    }
    document.getElementById('artist-claim-create')?.scrollIntoView({ behavior: 'smooth' });
  }

  claim(warehouseId: number): void {
    this.submit({ request_type: 'claim_ownership', warehouse_artist_id: warehouseId });
  }

  requestAccess(a: { id_artista: number }): void {
    this.submit({
      request_type: 'request_access',
      warehouse_artist_id: a.id_artista,
      proposed_role: 'member',
    });
  }

  createNew(): void {
    const name = this.createForm.value.name?.trim() || '';
    this.submit({ request_type: 'create_new', proposed_display_name: name });
  }

  private submit(body: Record<string, unknown>): void {
    this.error.set(null);
    this.message.set(null);
    this.api.createAccessRequest(body as never).subscribe({
      next: () => {
        this.message.set(this.i18n.t('artistSpace.claim.submitted'));
        this.reloadMine();
        void this.spaces.bootstrap({ force: true });
      },
      error: (e) => {
        const detail = e?.error?.detail;
        this.error.set(
          typeof detail === 'object' ? detail?.message : detail || e?.message || 'failed',
        );
      },
    });
  }

  cancel(id: number): void {
    this.api.cancelAccessRequest(id).subscribe({ next: () => this.reloadMine() });
  }

  private reloadMine(): void {
    this.api.listMyAccessRequests().subscribe({
      next: (rows) => this.mine.set(rows || []),
      error: () => undefined,
    });
  }
}
