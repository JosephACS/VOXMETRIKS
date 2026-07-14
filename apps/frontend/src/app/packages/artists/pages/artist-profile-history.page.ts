import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistStatusHistoryEntry } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-profile-history',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-profile-history-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a [routerLink]="['/artist-profiles', artistId]" class="back-link">
          {{ 'artists.history.back' | t:lang() }}
        </a>

        <app-enterprise-page-header [title]="'artists.history.title' | t:lang()" />

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (history.length === 0) {
          <app-enterprise-empty-state [title]="'artists.history.empty' | t:lang()" />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'artists.history.from' | t:lang() }}</th>
                  <th>{{ 'artists.history.to' | t:lang() }}</th>
                  <th>{{ 'artists.history.reason' | t:lang() }}</th>
                  <th>{{ 'artists.history.actor' | t:lang() }}</th>
                  <th>{{ 'artists.history.at' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (entry of history; track entry.id) {
                  <tr>
                    <td>{{ entry.from_status ?? '—' }}</td>
                    <td>
                      <app-enterprise-status-badge [status]="entry.to_status" />
                    </td>
                    <td>{{ entry.reason ?? '—' }}</td>
                    <td>{{ entry.actor_user_id ?? '—' }}</td>
                    <td>{{ entry.at | localeDate: true }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        }
      }
    </div>
  `,
})
export class ArtistProfileHistoryPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ArtistsApiService);
  private route = inject(ActivatedRoute);
  private orgCtx = inject(OrganizationContextService);

  history: ArtistStatusHistoryEntry[] = [];
  loading = false;
  error: string | null = null;
  orgId: number | null = null;

  get artistId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.loading = true;
    this.error = null;
    this.api.getHistory(orgId, this.artistId).subscribe({
      next: (items) => {
        this.history = items;
        this.loading = false;
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? this.i18n.t('common.failed');
      },
    });
  }
}
