import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { CatalogRelease } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-catalog-releases-list',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise catalog-releases-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'catalogRights.releases.title' | t:lang()"
          [subtitle]="'catalogRights.releases.subtitle' | t:lang()"
        />

        <app-enterprise-section-card [title]="'catalogRights.releases.create' | t:lang()">
          <form [formGroup]="createForm" (ngSubmit)="createRelease()" class="form-grid">
            <app-enterprise-form-field
              [label]="'catalogRights.releases.releaseTitle' | t:lang()"
              [required]="true"
            >
              <input formControlName="title" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'catalogRights.releases.warehouseAlbum' | t:lang()"
            >
              <input formControlName="warehouse_album_id" type="number" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
                {{ 'catalogRights.releases.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (releases.length === 0) {
          <app-enterprise-empty-state
            [title]="'catalogRights.releases.emptyTitle' | t:lang()"
            [description]="'catalogRights.releases.emptyBody' | t:lang()"
            [ctaLabel]="'catalogRights.releases.create' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'catalogRights.releases.releaseTitle' | t:lang() }}</th>
                  <th>{{ 'catalogRights.releases.warehouseLink' | t:lang() }}</th>
                  <th>{{ 'common.date' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (release of releases; track release.id) {
                  <tr>
                    <td>{{ release.title }}</td>
                    <td>
                      @if (release.warehouse_album_id) {
                        <span class="badge badge--linked">
                          {{ 'catalogRights.releases.linked' | t:lang() }}
                          (#{{ release.warehouse_album_id }})
                        </span>
                      } @else {
                        <span class="badge badge--unlinked">
                          {{ 'catalogRights.releases.notLinked' | t:lang() }}
                        </span>
                      }
                    </td>
                    <td>{{ release.created_at | localeDate:true }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
          <p class="muted">{{ 'campaigns.list.total' | t:lang() }}: {{ total }}</p>
        }
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
  orgId: number | null = null;

  createForm = this.fb.group({
    title: ['', [Validators.required]],
    warehouse_album_id: [null as number | null],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    const id = this.orgCtx.organizationId() ?? 0;
    this.orgId = id || null;
    if (!this.orgId) return;
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
        this.error = e.error?.message ?? this.i18n.t('common.loadFailed');
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
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.createFailed')),
      });
  }
}
