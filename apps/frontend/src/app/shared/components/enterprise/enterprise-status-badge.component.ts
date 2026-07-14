import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { StatusLabelPipe } from '../../pipes/status-label.pipe';

@Component({
  selector: 'app-enterprise-status-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [StatusLabelPipe],
  template: `
    <span [class]="'badge badge--' + status()">
      {{ label() ?? (status() | statusLabel) }}
    </span>
  `,
})
export class EnterpriseStatusBadgeComponent {
  readonly status = input.required<string>();
  readonly label = input<string | undefined>();
}
