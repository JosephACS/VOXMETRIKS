import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-enterprise-section-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="vx-card ent-section">
      @if (title() || subtitle()) {
        <header class="ent-section__header">
          @if (title()) {
            <h2 class="ent-section__title">{{ title() }}</h2>
          }
          @if (subtitle()) {
            <p class="ent-section__subtitle">{{ subtitle() }}</p>
          }
        </header>
      }
      <div class="ent-section__body">
        <ng-content />
      </div>
    </section>
  `,
})
export class EnterpriseSectionCardComponent {
  readonly title = input<string | undefined>();
  readonly subtitle = input<string | undefined>();
}
