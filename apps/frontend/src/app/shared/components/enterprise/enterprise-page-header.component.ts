import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-enterprise-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="vx-hero ent-header">
      <div class="ent-header__copy">
        <h1 class="vx-hero__title">{{ title() }}</h1>
        @if (subtitle()) {
          <p class="vx-hero__subtitle">{{ subtitle() }}</p>
        }
        @if (orgName() || badge()) {
          <div class="vx-hero__meta">
            @if (orgName()) {
              <span class="badge badge--active">{{ orgName() }}</span>
            }
            @if (badge()) {
              <span class="badge">{{ badge() }}</span>
            }
          </div>
        }
      </div>
      <div class="vx-hero__actions ent-header__actions">
        <ng-content />
      </div>
    </header>
  `,
})
export class EnterprisePageHeaderComponent {
  readonly title = input.required<string>();
  readonly subtitle = input<string | undefined>();
  readonly orgName = input<string | undefined>();
  readonly badge = input<string | undefined>();
}
