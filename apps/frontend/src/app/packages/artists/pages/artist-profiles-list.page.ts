import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistProfile } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-artist-profiles-list',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="artist-profiles-list-page">
      <h1>{{ 'artists.list.title' | t:lang() }}</h1>

      <div class="filters">
        <label>
          Status
          <select [value]="statusFilter" (change)="onStatusChange($event)">
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      </div>

      <form [formGroup]="createForm" (ngSubmit)="createArtist()" class="create-form">
        <input formControlName="display_name" placeholder="Artist display name" class="input" />
        <input formControlName="legal_name" placeholder="Legal name (optional)" class="input" />
        <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
          Create Artist Profile
        </button>
      </form>

      @if (error) {
        <p class="error">{{ error }}</p>
      }

      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (artists.length === 0) {
        <p>{{ 'artists.list.empty' | t:lang() }}</p>
      } @else {
        <table class="artists-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Warehouse Link</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            @for (artist of artists; track artist.id) {
              <tr>
                <td>{{ artist.display_name }}</td>
                <td><span class="badge" [class]="'badge--' + artist.status">{{ artist.status }}</span></td>
                <td>
                  @if (artist.warehouse_artist_id) {
                    <span class="badge badge--linked">Linked (#{{ artist.warehouse_artist_id }})</span>
                  } @else {
                    <span class="badge badge--unlinked">Not linked</span>
                  }
                </td>
                <td>
                  <a [routerLink]="['/artist-profiles', artist.id]">View</a>
                </td>
              </tr>
            }
          </tbody>
        </table>
        <p class="total">Total: {{ total }}</p>
      }
    </div>
  `,
})
export class ArtistProfilesListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ArtistsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  artists: ArtistProfile[] = [];
  total = 0;
  loading = false;
  error: string | null = null;
  statusFilter = '';

  createForm = this.fb.group({
    display_name: ['', [Validators.required]],
    legal_name: [''],
  });

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  ngOnInit(): void {
    this.load();
  }

  onStatusChange(event: Event): void {
    this.statusFilter = (event.target as HTMLSelectElement).value;
    this.load();
  }

  load(): void {
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.loading = true;
    this.api.list(this.orgId, { status: this.statusFilter || undefined }).subscribe({
      next: (res) => {
        this.artists = res.items;
        this.total = res.total;
        this.loading = false;
        this.error = null;
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? 'Error loading artist profiles';
      },
    });
  }

  createArtist(): void {
    if (this.createForm.invalid || !this.orgId) return;
    const value = this.createForm.value;
    this.api
      .create(this.orgId, {
        display_name: value.display_name!,
        legal_name: value.legal_name || null,
      })
      .subscribe({
        next: () => {
          this.createForm.reset();
          this.load();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error creating artist profile'),
      });
  }
}
