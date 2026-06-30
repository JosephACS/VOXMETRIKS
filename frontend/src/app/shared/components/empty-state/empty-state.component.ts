import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import {
  Component,
  inject,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
} from '@angular/core';

export type EmptyStateType = 'no-data' | 'no-results' | 'error' | 'loading';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="empty-state" [class]="'empty-type-' + type" role="status" [attr.aria-live]="type === 'loading' ? 'polite' : null">
      <div class="empty-icon" aria-hidden="true" [innerHTML]="iconSvg"></div>
      <div class="empty-title">{{ title }}</div>
      @if (description) {
        <p class="empty-description">{{ description }}</p>
      }
      @if (type === 'no-results' && searchTerm) {
        <p class="empty-term">{{ searchLabel }} "<strong>{{ searchTerm }}</strong>"</p>
        <button class="empty-action-btn" type="button" (click)="clearSearch.emit()">
          {{ clearSearchLabel }}
        </button>
      }
      @if (type === 'error') {
        <button class="empty-action-btn" type="button" (click)="retry.emit()">
          {{ retryLabel }}
        </button>
      }
    </div>
  `,
  styles: [`
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 3.5rem 1.5rem;
      text-align: center;
    }

    .empty-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      margin-bottom: 0.25rem;
      opacity: 0.55;
      color: var(--color-text-muted);
    }

    .empty-icon :deep(svg) { width: 32px; height: 32px; }

    .empty-title {
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--color-text-secondary);
    }

    .empty-description {
      font-size: 0.78rem;
      color: var(--color-text-muted);
      max-width: 320px;
    }

    .empty-term {
      font-size: 0.78rem;
      color: var(--color-text-muted);
    }

    .empty-term strong {
      color: var(--color-text-secondary);
    }

    .empty-type-error .empty-icon { opacity: 0.7; }
    .empty-type-error .empty-title { color: var(--color-danger); }

    .empty-action-btn {
      margin-top: 0.5rem;
      padding: 0.4rem 0.875rem;
      background: var(--color-surface-2);
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      color: var(--color-text-secondary);
      font-family: var(--font-body);
      font-size: 0.78rem;
      cursor: pointer;
      transition: border-color var(--transition-fast), color var(--transition-fast);
    }

    .empty-action-btn:hover {
      border-color: var(--color-primary);
      color: var(--color-primary);
    }
  `],
})
export class EmptyStateComponent {
  private iconRender = inject(IconRenderService);
  private i18n = inject(I18nService);

  @Input() type: EmptyStateType = 'no-data';
  @Input() searchTerm = '';
  @Input() customTitle?: string;
  @Input() customDescription?: string;

  @Output() clearSearch = new EventEmitter<void>();
  @Output() retry = new EventEmitter<void>();

  get iconSvg(): SafeHtml {
    return this.iconRender.render(this.iconKey, 32);
  }

  get iconKey(): string {
    switch (this.type) {
      case 'no-results': return 'search';
      case 'error':      return 'alert';
      case 'loading':    return 'loader';
      default:           return 'inbox';
    }
  }

  get title(): string {
    if (this.customTitle) return this.customTitle;
    switch (this.type) {
      case 'no-results': return this.i18n.t('empty.noResults');
      case 'error':      return this.i18n.t('empty.errorTitle');
      case 'loading':    return this.i18n.t('empty.loading');
      default:           return this.i18n.t('empty.noData');
    }
  }

  get description(): string {
    if (this.customDescription) return this.customDescription;
    switch (this.type) {
      case 'no-results': return this.i18n.t('empty.noResultsDesc');
      case 'error':      return this.i18n.t('empty.errorDesc');
      default:           return '';
    }
  }

  get searchLabel(): string {
    return this.i18n.t('empty.searchLabel');
  }

  get clearSearchLabel(): string {
    return this.i18n.t('empty.clearSearch');
  }

  get retryLabel(): string {
    return this.i18n.t('common.retry');
  }
}
