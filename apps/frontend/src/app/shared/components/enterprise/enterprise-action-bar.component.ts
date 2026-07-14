import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-enterprise-action-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="vx-actions ent-action-bar">
      <ng-content />
    </div>
  `,
})
export class EnterpriseActionBarComponent {}
