import { Component, Input } from '@angular/core';
import { TranslationKey } from '../../../core/i18n/translations';
import { TranslatePipe } from '../../pipes/translate.pipe';

export type DataSourceKind = 'live' | 'local' | 'synthetic' | 'mixed' | 'demo';

const LABEL_KEYS: Record<DataSourceKind, TranslationKey> = {
  live: 'data.live',
  local: 'data.local',
  synthetic: 'data.synthetic',
  mixed: 'data.mixed',
  demo: 'data.demo',
};

@Component({
  selector: 'app-data-source-badge',
  standalone: true,
  imports: [TranslatePipe],
  template: `
    <span class="data-source-badge" [class]="'data-source-badge--' + kind">
      {{ labelKey | t }}
    </span>
  `,
  styles: [`
    .data-source-badge {
      display: inline-flex;
      align-items: center;
      font-size: 0.625rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 0.18rem 0.45rem;
      border-radius: 999px;
      line-height: 1.2;
      white-space: nowrap;
    }
    .data-source-badge--live {
      color: var(--accent, #1ed896);
      background: rgba(30, 216, 150, 0.12);
      border: 1px solid rgba(30, 216, 150, 0.28);
    }
    .data-source-badge--local {
      color: #60a5fa;
      background: rgba(96, 165, 250, 0.12);
      border: 1px solid rgba(96, 165, 250, 0.28);
    }
    .data-source-badge--synthetic {
      color: #fbbf24;
      background: rgba(251, 191, 36, 0.12);
      border: 1px solid rgba(251, 191, 36, 0.28);
    }
    .data-source-badge--mixed {
      color: #c084fc;
      background: rgba(192, 132, 252, 0.12);
      border: 1px solid rgba(192, 132, 252, 0.28);
    }
    .data-source-badge--demo {
      color: var(--play-btn-fg, #000);
      background: var(--accent, #1ed896);
      border: 1px solid transparent;
    }
  `],
})
export class DataSourceBadgeComponent {
  @Input({ required: true }) kind: DataSourceKind = 'live';

  get labelKey(): TranslationKey {
    return LABEL_KEYS[this.kind];
  }
}
