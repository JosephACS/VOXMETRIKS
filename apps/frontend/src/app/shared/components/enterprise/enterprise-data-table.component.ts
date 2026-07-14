import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { I18nService } from '../../../core/services/i18n.service';

@Component({
  selector: 'app-enterprise-data-table',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="table-card ent-data-table">
      <div class="ent-data-table-toolbar">
        <ng-content select="[toolbar]" />
      </div>
      @if (empty()) {
        <div class="empty-state ent-empty" role="status">
          <div class="ent-empty__title">{{ emptyTitle() || i18n.t('common.empty') }}</div>
          @if (emptyDescription()) {
            <p class="ent-empty__description">{{ emptyDescription() }}</p>
          }
        </div>
      } @else {
        <div class="table-scroll">
          <ng-content />
        </div>
      }
    </div>
  `,
})
export class EnterpriseDataTableComponent {
  readonly i18n = inject(I18nService);
  readonly empty = input(false);
  readonly emptyTitle = input<string | undefined>();
  readonly emptyDescription = input<string | undefined>();
}
