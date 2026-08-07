import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistAccessRequest } from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-platform-artist-requests',
  standalone: true,
  imports: [CommonModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.platform.title' | t:lang()"
        [subtitle]="'artistSpace.platform.subtitle' | t:lang()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (items().length === 0) {
        <app-enterprise-empty-state
          [title]="'artistSpace.platform.emptyTitle' | t:lang()"
          [description]="'artistSpace.platform.emptyBody' | t:lang()"
        />
      } @else {
        @for (r of items(); track r.id) {
          <app-enterprise-section-card [title]="'#' + r.id + ' — ' + r.request_type">
            <p>
              applicant {{ r.applicant_user_id }}
              @if (r.warehouse_artist_id) {
                · warehouse {{ r.warehouse_artist_id }}
              }
              @if (r.proposed_display_name) {
                · {{ r.proposed_display_name }}
              }
            </p>
            <div class="actions">
              <button type="button" class="btn btn--primary" (click)="approve(r)">
                {{ 'common.approve' | t:lang() }}
              </button>
              <button type="button" class="btn btn--secondary" (click)="reject(r)">
                {{ 'common.reject' | t:lang() }}
              </button>
            </div>
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
  styles: [
    `
      .actions {
        display: flex;
        gap: 0.5rem;
      }
    `,
  ],
})
export class PlatformArtistRequestsPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<ArtistAccessRequest[]>([]);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.listPlatformRequests('pending').subscribe({
      next: (rows) => {
        this.items.set(rows || []);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.message || 'load_failed');
        this.loading.set(false);
      },
    });
  }

  approve(r: ArtistAccessRequest): void {
    this.api.approvePlatformRequest(r.id).subscribe({ next: () => this.load() });
  }

  reject(r: ArtistAccessRequest): void {
    this.api.rejectPlatformRequest(r.id).subscribe({ next: () => this.load() });
  }
}
