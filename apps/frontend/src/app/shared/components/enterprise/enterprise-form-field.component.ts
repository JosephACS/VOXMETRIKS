import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-enterprise-form-field',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="form-field ent-form-field" [class.ent-form-field--error]="!!error()">
      <label class="ent-form-field__label">
        <span>
          {{ label() }}
          @if (required()) {
            <span class="ent-form-field__req" aria-hidden="true">*</span>
          }
        </span>
        <ng-content />
      </label>
      @if (error()) {
        <p class="ent-form-field__error" role="alert">{{ error() }}</p>
      } @else if (hint()) {
        <p class="ent-form-field__hint">{{ hint() }}</p>
      }
    </div>
  `,
})
export class EnterpriseFormFieldComponent {
  readonly label = input.required<string>();
  readonly hint = input<string | undefined>();
  readonly error = input<string | undefined>();
  readonly required = input(false);
}
