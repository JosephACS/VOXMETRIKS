import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-invite-accept',
  standalone: true,
  imports: [CommonModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.inviteAccept.title' | t:lang()"
        [subtitle]="'artistSpace.inviteAccept.subtitle' | t:lang()"
      />
      @if (status() === 'loading') {
        <app-enterprise-loading-skeleton [rows]="2" />
      } @else if (status() === 'ok') {
        <app-enterprise-empty-state
          [title]="'artistSpace.inviteAccept.success' | t:lang()"
          [description]="'artistSpace.inviteAccept.successBody' | t:lang()"
          [ctaLabel]="'artistSpace.inviteAccept.go' | t:lang()"
          ctaLink="/artist-space"
        />
      } @else {
        <app-enterprise-error-state [message]="error() || 'failed'" (retry)="accept()" />
      }
    </div>
  `,
})
export class ArtistInviteAcceptPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ArtistSpaceApiService);
  private readonly spaces = inject(SpaceContextService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly status = signal<'loading' | 'ok' | 'error'>('loading');
  readonly error = signal<string | null>(null);
  private token = '';

  ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token') || '';
    this.accept();
  }

  accept(): void {
    if (!this.token) {
      this.status.set('error');
      this.error.set('missing_token');
      return;
    }
    this.status.set('loading');
    this.api.acceptInvitation(this.token).subscribe({
      next: async () => {
        this.status.set('ok');
        await this.spaces.bootstrap({ force: true });
      },
      error: (e) => {
        this.status.set('error');
        const detail = e?.error?.detail;
        this.error.set(
          typeof detail === 'object' ? detail?.message : detail || e?.message || 'failed',
        );
      },
    });
  }
}
