import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ModuleContextView } from '../navigation/module-context';

/**
 * Compact module chrome: breadcrumb + secondary tabs.
 * Sibling navigation uses tabs; detail uses breadcrumbs — no redundant “Volver a…”.
 */
@Component({
  selector: 'app-module-context-chrome',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (context && (visibleCrumbs.length || context.tabs.length || context.hubLabel)) {
      <div class="mod-chrome" [attr.data-module]="context.moduleId">
        @if (context.hubLabel && context.tabs.length) {
          <p class="mod-chrome__hub-label">{{ context.hubLabel }}</p>
        }

        @if (visibleCrumbs.length) {
          <nav class="mod-chrome__crumbs" aria-label="Ruta de navegación">
            <ol class="mod-chrome__crumb-list">
              @for (c of visibleCrumbs; track $index; let last = $last) {
                <li class="mod-chrome__crumb">
                  @if (!last && c.path) {
                    <a [routerLink]="c.path" [queryParams]="c.queryParams || {}">{{ c.label }}</a>
                  } @else if (!last) {
                    <span>{{ c.label }}</span>
                  } @else {
                    <span class="current" aria-current="page">{{ c.label }}</span>
                  }
                  @if (!last) {
                    <span class="mod-chrome__sep" aria-hidden="true">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </span>
                  }
                </li>
              }
            </ol>
          </nav>
        }

        @if (context.tabs.length) {
          <nav
            class="mod-chrome__tabs"
            role="tablist"
            [attr.aria-label]="'Secciones de ' + context.hubLabel"
          >
            @for (tab of context.tabs; track tab.path) {
              <a
                class="mod-chrome__tab"
                role="tab"
                [class.is-active]="tab.path === context.activeTabPath"
                [attr.aria-selected]="tab.path === context.activeTabPath"
                [routerLink]="tab.path"
              >
                {{ tab.label }}
              </a>
            }
          </nav>
        }
      </div>
    }
  `,
  styles: [
    `
      .mod-chrome {
        margin: 0 0 0.85rem;
        max-width: 1200px;
      }
      .mod-chrome__hub-label {
        margin: 0 0 0.35rem;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--shell-fg-subtle, var(--text-muted, rgba(255, 255, 255, 0.45)));
      }
      .mod-chrome__crumbs {
        margin: 0 0 0.55rem;
      }
      .mod-chrome__crumb-list {
        display: flex;
        flex-wrap: nowrap;
        align-items: center;
        gap: 0.15rem;
        margin: 0;
        padding: 0;
        list-style: none;
        font-size: 0.78rem;
        line-height: 1.35;
        color: var(--shell-fg-subtle, var(--text-muted, rgba(255, 255, 255, 0.5)));
        overflow: hidden;
      }
      .mod-chrome__crumb {
        display: inline-flex;
        align-items: center;
        gap: 0.15rem;
        min-width: 0;
      }
      .mod-chrome__crumb a,
      .mod-chrome__crumb > span:not(.mod-chrome__sep) {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 14rem;
      }
      .mod-chrome__crumbs a {
        color: var(--shell-fg-muted, var(--text-muted, rgba(255, 255, 255, 0.7)));
        text-decoration: none;
        font-weight: 500;
      }
      .mod-chrome__crumbs a:hover {
        color: var(--accent, #e8a33d);
      }
      .mod-chrome__crumbs a:focus-visible {
        outline: 2px solid var(--accent, #e8a33d);
        outline-offset: 2px;
        border-radius: 2px;
      }
      .mod-chrome__crumbs .current {
        color: var(--shell-fg, var(--text, #fff));
        font-weight: 600;
      }
      .mod-chrome__sep {
        display: inline-flex;
        flex-shrink: 0;
        opacity: 0.45;
        color: var(--shell-fg-subtle, rgba(255, 255, 255, 0.45));
      }
      .mod-chrome__tabs {
        display: flex;
        flex-wrap: nowrap;
        gap: 0.3rem;
        padding: 0.2rem;
        background: var(--shell-control-bg, rgba(255, 255, 255, 0.04));
        border: 1px solid var(--shell-border, rgba(255, 255, 255, 0.06));
        border-radius: 8px;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        max-width: 100%;
      }
      .mod-chrome__tab {
        flex: 0 0 auto;
        text-decoration: none;
        color: var(--shell-fg-muted, rgba(255, 255, 255, 0.65));
        padding: 0.4rem 0.75rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        white-space: nowrap;
      }
      .mod-chrome__tab:hover {
        color: var(--shell-fg, #fff);
        background: var(--shell-hover, rgba(255, 255, 255, 0.06));
      }
      .mod-chrome__tab:focus-visible {
        outline: 2px solid var(--accent, #e8a33d);
        outline-offset: 1px;
      }
      .mod-chrome__tab.is-active {
        color: var(--bg-base, #0a0a0a);
        background: var(--accent, #e8a33d);
      }
      :host-context([data-theme='light']) .mod-chrome__tab.is-active {
        color: #04140f;
      }
      @media (max-width: 640px) {
        .mod-chrome__crumb a,
        .mod-chrome__crumb > span:not(.mod-chrome__sep) {
          max-width: 8.5rem;
        }
        .mod-chrome__crumbs {
          font-size: 0.72rem;
        }
      }
    `,
  ],
})
export class ModuleContextChromeComponent {
  @Input({ required: true }) context!: ModuleContextView;

  get visibleCrumbs() {
    const crumbs = this.context?.crumbs ?? [];
    if (crumbs.length <= 3) return crumbs;
    return [crumbs[0], ...crumbs.slice(-2)];
  }
}
