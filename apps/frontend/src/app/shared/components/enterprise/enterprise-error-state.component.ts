import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

@Component({
  selector: 'app-enterprise-error-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="alert alert--danger ent-error" role="alert">
      <p class="ent-error__message">{{ message() }}</p>
      <button type="button" class="btn btn--secondary" (click)="retry.emit()">
        {{ retryLabel() || 'Reintentar' }}
      </button>
    </div>
  `,
})
export class EnterpriseErrorStateComponent {
  readonly message = input.required<string>();
  readonly retryLabel = input<string | undefined>();
  readonly retry = output<void>();
}
