import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject, Input } from '@angular/core';
import { TranslationKey } from '../../../core/i18n/translations';
import { TranslatePipe } from '../../pipes/translate.pipe';

export type DataSourceKind = 'live' | 'local' | 'synthetic' | 'mixed' | 'demo';

const LABEL_KEYS: Record<DataSourceKind, TranslationKey> = {
  live: 'data.live',
  local: 'data.local',
  synthetic: 'data.synthetic',
  mixed: 'data.mixed',
  // Legacy kind — same user-facing label as synthetic (avoid "Demo" copy).
  demo: 'data.synthetic',
};

@Component({
  selector: 'app-data-source-badge',
  standalone: true,
  imports: [TranslatePipe],
  template: `
    <span class="data-source-badge" [class]="'data-source-badge--' + kind">
      {{ labelKey | t:lang() }}
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
      color: var(--accent, #e8a33d);
      background: rgba(232, 163, 61, 0.12);
      border: 1px solid rgba(232, 163, 61, 0.28);
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
      color: var(--accent-hover, #f0b555);
      background: color-mix(in srgb, var(--accent) 12%, transparent);
      border: 1px solid color-mix(in srgb, var(--accent) 28%, transparent);
    }
    .data-source-badge--demo {
      color: var(--play-btn-fg, #000);
      background: var(--accent, #e8a33d);
      border: 1px solid transparent;
    }
  `],
})
export class DataSourceBadgeComponent {
  readonly lang = inject(I18nService).lang;
  @Input({ required: true }) kind: DataSourceKind = 'live';

  get labelKey(): TranslationKey {
    return LABEL_KEYS[this.kind];
  }
}
