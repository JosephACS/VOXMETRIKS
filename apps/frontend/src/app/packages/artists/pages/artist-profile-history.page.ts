import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistStatusHistoryEntry } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-artist-profile-history',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="artist-profile-history-page">
      <a [routerLink]="['/artist-profiles', artistId]">&larr; Back to profile</a>
      <h1>{{ 'artists.history.title' | t:lang() }}</h1>

      @if (history.length === 0) {
        <p>{{ 'artists.history.empty' | t:lang() }}</p>
      } @else {
        <table class="history-table">
          <thead>
            <tr>
              <th>From</th>
              <th>To</th>
              <th>Reason</th>
              <th>Actor</th>
              <th>At</th>
            </tr>
          </thead>
          <tbody>
            @for (entry of history; track entry.id) {
              <tr>
                <td>{{ entry.from_status ?? '—' }}</td>
                <td><span class="badge" [class]="'badge--' + entry.to_status">{{ entry.to_status }}</span></td>
                <td>{{ entry.reason ?? '—' }}</td>
                <td>{{ entry.actor_user_id ?? '—' }}</td>
                <td>{{ entry.at | date: 'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
      }

      @if (error) {
        <p class="error">{{ error }}</p>
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
  error: string | null = null;

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  get artistId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.api.getHistory(this.orgId, this.artistId).subscribe({
      next: (items) => (this.history = items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading history'),
    });
  }
}
