import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-invite-accept',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.inviteAccept.title' | t:lang()"
        [subtitle]="'artistSpace.inviteAccept.subtitle' | t:lang()"
      />
      @if (status() === 'ok') {
        <app-enterprise-empty-state
          [title]="'artistSpace.inviteAccept.success' | t:lang()"
          [description]="'artistSpace.inviteAccept.successBody' | t:lang()"
          [ctaLabel]="'artistSpace.inviteAccept.go' | t:lang()"
          ctaLink="/artist-space"
        />
      } @else {
        <app-enterprise-section-card [title]="'artistSpace.inviteAccept.pasteTitle' | t:lang()">
          <p>{{ 'artistSpace.inviteAccept.pasteHint' | t:lang() }}</p>
          <form [formGroup]="form" (ngSubmit)="accept()" class="form-grid">
            <app-enterprise-form-field
              [label]="'artistSpace.inviteAccept.tokenLabel' | t:lang()"
              [required]="true"
            >
              <input
                class="input"
                formControlName="token"
                type="text"
                autocomplete="off"
                spellcheck="false"
              />
            </app-enterprise-form-field>
            <button
              type="submit"
              class="btn btn--primary"
              [disabled]="form.invalid || status() === 'loading'"
            >
              {{ 'artistSpace.inviteAccept.submit' | t:lang() }}
            </button>
          </form>
          @if (status() === 'error' && error()) {
            <app-enterprise-error-state [message]="error()!" (retry)="accept()" />
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class ArtistInviteAcceptPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly spaces = inject(SpaceContextService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);

  readonly lang = this.i18n.lang;
  readonly status = signal<'idle' | 'loading' | 'ok' | 'error'>('idle');
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    token: ['', Validators.required],
  });

  ngOnInit(): void {
    const state = window.history.state as { invitationToken?: unknown } | null;
    const token = typeof state?.invitationToken === 'string' ? state.invitationToken.trim() : '';
    if (token) this.form.controls.token.setValue(token);
  }

  accept(): void {
    const token = this.form.getRawValue().token.trim();
    if (!token) {
      this.status.set('error');
      this.error.set(this.i18n.t('artistSpace.inviteAccept.missingToken'));
      return;
    }
    this.status.set('loading');
    this.error.set(null);
    this.api.acceptInvitation(token).subscribe({
      next: async () => {
        this.status.set('ok');
        await this.spaces.bootstrap({ force: true });
      },
      error: (e) => {
        this.status.set('error');
        const detail = e?.error?.detail;
        const message =
          typeof detail === 'object' ? detail?.message : detail || e?.message || 'failed';
        this.error.set(String(message));
      },
    });
  }
}
