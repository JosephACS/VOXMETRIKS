import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { CatalogRelease } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-catalog-releases-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="vx-enterprise catalog-releases-list-page">
      <h1>{{ 'catalogRights.releases.title' | t:lang() }}</h1>
      <p class="subtitle">
        Release records (e.g. albums/EPs) tracked for rights purposes. Optional warehouse album
        reference only — dim_album data is never duplicated here.
      </p>

      <form [formGroup]="createForm" (ngSubmit)="createRelease()" class="create-form">
        <input formControlName="title" placeholder="Release title" class="input" />
        <input formControlName="warehouse_album_id" type="number" placeholder="Warehouse album id (optional)" class="input" />
        <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
          Create Release
        </button>
      </form>

      @if (error) {
        <p class="error">{{ error }}</p>
      }

      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (releases.length === 0) {
        <p>{{ 'catalogRights.releases.empty' | t:lang() }}</p>
      } @else {
        <table class="releases-table">
          <thead>
            <tr><th>Title</th><th>Warehouse Album Link</th><th>Created</th></tr>
          </thead>
          <tbody>
            @for (release of releases; track release.id) {
              <tr>
                <td>{{ release.title }}</td>
                <td>
                  @if (release.warehouse_album_id) {
                    <span class="badge badge--linked">Linked (#{{ release.warehouse_album_id }})</span>
                  } @else {
                    <span class="badge badge--unlinked">Not linked</span>
                  }
                </td>
                <td>{{ release.created_at | date:'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
        <p class="total">Total: {{ total }}</p>
      }
    </div>
  `,
})
export class CatalogReleasesListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  releases: CatalogRelease[] = [];
  total = 0;
  loading = false;
  error: string | null = null;

  createForm = this.fb.group({
    title: ['', [Validators.required]],
    warehouse_album_id: [null as number | null],
  });

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.loading = true;
    this.api.listReleases(this.orgId).subscribe({
      next: (res) => {
        this.releases = res.items;
        this.total = res.total;
        this.loading = false;
        this.error = null;
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? 'Error loading releases';
      },
    });
  }

  createRelease(): void {
    if (this.createForm.invalid || !this.orgId) return;
    const value = this.createForm.value;
    this.api
      .createRelease(this.orgId, {
        title: value.title!,
        warehouse_album_id: value.warehouse_album_id || null,
      })
      .subscribe({
        next: () => {
          this.createForm.reset();
          this.load();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error creating release'),
      });
  }
}
