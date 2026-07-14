import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-enterprise-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <div class="empty-state ent-empty" role="status">
      @if (icon()) {
        <div class="ent-empty__icon" aria-hidden="true">{{ icon() }}</div>
      }
      <div class="ent-empty__title">{{ title() }}</div>
      @if (description()) {
        <p class="ent-empty__description">{{ description() }}</p>
      }
      @if (ctaLabel()) {
        @if (ctaLink()) {
          <a
            class="btn btn--primary"
            [routerLink]="ctaLink()!"
            (click)="ctaClick.emit()"
          >
            {{ ctaLabel() }}
          </a>
        } @else {
          <button type="button" class="btn btn--primary" (click)="ctaClick.emit()">
            {{ ctaLabel() }}
          </button>
        }
      }
    </div>
  `,
})
export class EnterpriseEmptyStateComponent {
  readonly title = input.required<string>();
  readonly description = input<string | undefined>();
  readonly ctaLabel = input<string | undefined>();
  readonly ctaLink = input<string | undefined>();
  readonly icon = input<string | undefined>();
  readonly ctaClick = output<void>();
}
