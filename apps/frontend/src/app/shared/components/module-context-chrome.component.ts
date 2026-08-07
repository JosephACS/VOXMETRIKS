import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ModuleContextView } from '../navigation/module-context';

/**
 * Compact module chrome: back + breadcrumb + secondary tabs (043 hotfix).
 */
@Component({
  selector: 'app-module-context-chrome',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (context) {
      <div class="mod-chrome" [attr.data-module]="context.moduleId">
        <div class="mod-chrome__top">
          @if (context.showBack) {
            <a
              class="mod-chrome__back"
              [routerLink]="context.hubPath"
              [queryParams]="context.hubQueryParams || {}"
            >
              ← {{ context.backLabel }}
            </a>
          } @else {
            <span class="mod-chrome__hub-label">{{ context.hubLabel }}</span>
          }
          @if (context.secondaryBack) {
            <a
              class="mod-chrome__back mod-chrome__back--secondary"
              [routerLink]="context.secondaryBack.path"
              [queryParams]="context.secondaryBack.queryParams || {}"
            >
              ← {{ context.secondaryBack.label }}
            </a>
          }
        </div>

        <nav class="mod-chrome__crumbs" aria-label="Ruta de navegación">
          @for (c of context.crumbs; track $index; let last = $last) {
            @if (!last && c.path) {
              <a [routerLink]="c.path" [queryParams]="c.queryParams || {}">{{ c.label }}</a>
              <span class="sep" aria-hidden="true">/</span>
            } @else if (!last) {
              <span>{{ c.label }}</span>
              <span class="sep" aria-hidden="true">/</span>
            } @else {
              <span class="current" aria-current="page">{{ c.label }}</span>
            }
          }
        </nav>

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
      .mod-chrome__top {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.65rem 1rem;
        margin-bottom: 0.35rem;
      }
      .mod-chrome__back {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--accent, #1ed896);
        text-decoration: none;
        white-space: nowrap;
      }
      .mod-chrome__back:hover {
        text-decoration: underline;
      }
      .mod-chrome__back--secondary {
        color: var(--color-text-secondary, rgba(255, 255, 255, 0.65));
      }
      .mod-chrome__hub-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
      }
      .mod-chrome__crumbs {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.78rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.5));
        margin-bottom: 0.55rem;
        line-height: 1.35;
      }
      .mod-chrome__crumbs a {
        color: var(--color-text-secondary, rgba(255, 255, 255, 0.7));
        text-decoration: none;
      }
      .mod-chrome__crumbs a:hover {
        color: var(--accent, #1ed896);
      }
      .mod-chrome__crumbs .current {
        color: var(--color-text, #fff);
        font-weight: 600;
      }
      .sep {
        opacity: 0.45;
      }
      .mod-chrome__tabs {
        display: flex;
        flex-wrap: nowrap;
        gap: 0.3rem;
        padding: 0.2rem;
        background: var(--color-surface-3, rgba(255, 255, 255, 0.04));
        border-radius: 8px;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        max-width: 100%;
      }
      .mod-chrome__tab {
        flex: 0 0 auto;
        text-decoration: none;
        color: var(--color-text-secondary, rgba(255, 255, 255, 0.65));
        padding: 0.4rem 0.75rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        white-space: nowrap;
      }
      .mod-chrome__tab:hover {
        color: var(--color-text, #fff);
        background: rgba(255, 255, 255, 0.06);
      }
      .mod-chrome__tab.is-active {
        color: var(--bg-base, #0a0a0a);
        background: var(--accent, #1ed896);
      }
      @media (max-width: 640px) {
        .mod-chrome__top {
          flex-direction: column;
          align-items: flex-start;
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
}
