import {
  Component,
  ElementRef,
  HostListener,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { AppSpace } from '../../../core/spaces/space.models';
import { TranslatePipe } from '../../pipes/translate.pipe';

/**
 * Academic-period style space switcher (045).
 * Shown only when more than one space is available (parent gates visibility).
 * Does not expose roles or permission codes.
 */
@Component({
  selector: 'app-space-selector',
  standalone: true,
  imports: [CommonModule, TranslatePipe],
  template: `
    <div class="space-selector" data-testid="space-selector">
      <button
        type="button"
        class="space-selector-btn"
        #trigger
        (click)="toggle()"
        [attr.aria-expanded]="open()"
        [attr.aria-label]="'spaces.selector.open' | t"
      >
        <span class="space-selector-kind" aria-hidden="true">{{ kindGlyph(active()?.kind) }}</span>
        <span class="space-selector-name">{{ active()?.label || ('spaces.personal' | t) }}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      @if (open()) {
        <div class="space-selector-menu" role="listbox" [attr.aria-label]="'spaces.selector.label' | t">
          <div class="space-selector-current">
            <span class="space-selector-current-label">{{ 'spaces.selector.current' | t }}</span>
            <span class="space-selector-current-name">{{ active()?.label }}</span>
          </div>
          <div class="space-selector-list">
            @for (space of spaces(); track space.id) {
              <button
                type="button"
                class="space-selector-item"
                role="option"
                [attr.data-testid]="'space-selector-item-' + space.kind"
                [class.space-selector-item--active]="space.id === active()?.id"
                [attr.aria-selected]="space.id === active()?.id"
                (click)="choose(space)"
              >
                <span class="space-selector-item-row">
                  <span aria-hidden="true">{{ kindGlyph(space.kind) }}</span>
                  <span class="space-selector-item-name">{{ space.label }}</span>
                </span>
              </button>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [
    `
      .space-selector {
        position: relative;
        margin-right: 0.75rem;
      }
      .space-selector-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        max-width: 260px;
        padding: 0.35rem 0.65rem;
        border-radius: 8px;
        border: 1px solid var(--border, #30363d);
        background: transparent;
        color: inherit;
        font: inherit;
        cursor: pointer;
      }
      .space-selector-btn:focus-visible {
        outline: 2px solid #1ed896;
        outline-offset: 2px;
      }
      .space-selector-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 600;
        font-size: 0.875rem;
      }
      .space-selector-kind {
        opacity: 0.75;
        font-size: 0.75rem;
      }
      .space-selector-menu {
        position: absolute;
        right: 0;
        top: calc(100% + 0.35rem);
        width: min(300px, 92vw);
        z-index: 50;
        border-radius: 10px;
        border: 1px solid var(--shell-border-strong, var(--border, #30363d));
        background: var(--shell-dropdown, var(--color-surface, #161b22));
        color: var(--shell-fg, var(--color-text, #e7edea));
        padding: 0.35rem;
        box-shadow: var(--shadow-md, 0 8px 24px rgba(0, 0, 0, 0.35));
      }
      .space-selector-current {
        padding: 0.45rem 0.65rem 0.55rem;
        border-bottom: 1px solid var(--shell-border, rgba(255, 255, 255, 0.08));
        margin-bottom: 0.25rem;
      }
      .space-selector-current-label {
        display: block;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--shell-fg-subtle, rgba(231, 237, 234, 0.55));
        margin-bottom: 0.15rem;
      }
      .space-selector-current-name {
        font-weight: 600;
        font-size: 0.875rem;
        color: var(--shell-fg, inherit);
      }
      .space-selector-list {
        max-height: 240px;
        overflow-y: auto;
      }
      .space-selector-item {
        display: flex;
        width: 100%;
        text-align: left;
        padding: 0.55rem 0.65rem;
        border: 0;
        border-radius: 8px;
        background: transparent;
        color: var(--shell-fg, inherit);
        font: inherit;
        cursor: pointer;
      }
      .space-selector-item:hover,
      .space-selector-item:focus-visible {
        background: var(--shell-hover-strong, color-mix(in srgb, #1ed896 12%, transparent));
        outline: none;
      }
      .space-selector-item--active {
        font-weight: 700;
        background: color-mix(in srgb, var(--accent, #1ed896) 18%, transparent);
      }
      .space-selector-item-row {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        width: 100%;
      }
      .space-selector-item-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    `,
  ],
})
export class SpaceSelectorComponent {
  private readonly spacesCtx = inject(SpaceContextService);
  private readonly host = inject(ElementRef<HTMLElement>);

  @ViewChild('trigger') trigger?: ElementRef<HTMLButtonElement>;

  readonly open = signal(false);
  readonly spaces = this.spacesCtx.availableSpaces;
  readonly active = this.spacesCtx.activeSpace;

  toggle(): void {
    this.open.update((v) => !v);
  }

  async choose(space: AppSpace): Promise<void> {
    this.open.set(false);
    if (space.id === this.active()?.id) return;
    // Intentionally does not stop the global player (SpaceContextService).
    await this.spacesCtx.selectSpace(space.id, { navigate: true });
  }

  kindGlyph(kind: AppSpace['kind'] | undefined): string {
    switch (kind) {
      case 'organization':
        return '⌂';
      case 'data_ops':
        return '⬡';
      case 'platform_admin':
        return '⚙';
      case 'artist':
        return '♪';
      default:
        return '●';
    }
  }

  @HostListener('document:click', ['$event'])
  onDocClick(ev: MouseEvent): void {
    if (!this.open()) return;
    const t = ev.target as Node | null;
    if (t && this.host.nativeElement.contains(t)) return;
    this.open.set(false);
  }

  @HostListener('document:keydown.escape')
  onEsc(): void {
    this.open.set(false);
  }
}
