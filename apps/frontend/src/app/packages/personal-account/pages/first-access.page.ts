import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-first-access-page',
  standalone: true,
  imports: [TranslatePipe],
  template: `
    <section class="vx-enterprise vx-choice-page" data-testid="first-access-page">
      <h1 class="vx-choice-page__title">{{ 'firstAccess.title' | t:lang() }}</h1>
      <p class="vx-choice-page__subtitle">{{ 'firstAccess.subtitle' | t:lang() }}</p>
      <div class="vx-choice-page__options">
        <button type="button" class="org-btn" data-testid="first-access-listen" (click)="choose('listen')">
          {{ 'firstAccess.listen' | t:lang() }}
        </button>
        <button type="button" class="org-btn" data-testid="first-access-artist" (click)="choose('artist')">
          {{ 'firstAccess.artist' | t:lang() }}
        </button>
        <button type="button" class="org-btn" data-testid="first-access-org" (click)="choose('organization')">
          {{ 'firstAccess.organization' | t:lang() }}
        </button>
      </div>
    </section>
  `,
  styleUrls: ['../../../core/spaces/styles/choice-page.css'],
})
export class FirstAccessPage {
  private readonly i18n = inject(I18nService);
  private readonly spaces = inject(SpaceContextService);
  private readonly router = inject(Router);
  readonly lang = this.i18n.lang;

  async choose(intent: 'listen' | 'artist' | 'organization'): Promise<void> {
    await this.spaces.completeFirstAccess(intent);
    if (intent === 'artist') {
      await this.router.navigateByUrl('/artist-space/claim');
      return;
    }
    if (intent === 'organization') {
      await this.router.navigateByUrl('/organizations/new');
      return;
    }
    await this.router.navigateByUrl('/discover');
  }
}
