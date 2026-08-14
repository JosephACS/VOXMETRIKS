import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { I18nService } from '../../services/i18n.service';
import { SpaceContextService } from '../space-context.service';
import { homePathForSpace } from '../space.models';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-space-chooser-page',
  standalone: true,
  imports: [TranslatePipe],
  template: `
    <section class="vx-enterprise vx-choice-page" data-testid="space-chooser-page">
      <h1 class="vx-choice-page__title">{{ 'spaceChooser.title' | t:lang() }}</h1>
      <p class="vx-choice-page__subtitle">{{ 'spaceChooser.subtitle' | t:lang() }}</p>

      @if (spaces.status() === 'error') {
        <p class="vx-choice-page__empty" role="alert" data-testid="space-chooser-error">
          {{ 'spaceChooser.loadError' | t:lang() }}
        </p>
        <div class="vx-choice-page__options">
          <button type="button" class="org-btn" data-testid="space-chooser-retry" (click)="retry()">
            {{ 'spaceChooser.retry' | t:lang() }}
          </button>
        </div>
      } @else {
        <div class="vx-choice-page__options">
          @for (space of spaces.availableSpaces(); track space.id) {
            <button
              type="button"
              class="org-btn"
              [attr.data-testid]="'space-choice-' + space.kind"
              (click)="choose(space.id)"
            >
              {{ space.label }}
            </button>
          }
        </div>
      }
    </section>
  `,
  styleUrls: ['../styles/choice-page.css'],
})
export class SpaceChooserPage {
  private readonly i18n = inject(I18nService);
  readonly spaces = inject(SpaceContextService);
  private readonly router = inject(Router);
  readonly lang = this.i18n.lang;

  async choose(spaceId: string): Promise<void> {
    const ok = await this.spaces.selectSpace(spaceId, { navigate: false });
    if (!ok) return;
    const active = this.spaces.activeSpace();
    await this.router.navigateByUrl(active ? homePathForSpace(active) : '/discover');
  }

  async retry(): Promise<void> {
    await this.spaces.bootstrap({ force: true });
  }
}
