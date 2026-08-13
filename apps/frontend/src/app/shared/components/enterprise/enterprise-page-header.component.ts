import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * Lightweight enterprise page header (Reports pilot).
 * One back · one quiet badge · title · lede. No duplicated crumbs.
 */
@Component({
  selector: 'app-enterprise-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <header class="vx-ent-page-header" [class.vx-ent-page-header--report]="reportMode()">
      @if (backPath() || badge() || reportMode()) {
        <div class="vx-ent-page-header__nav">
          @if (backPath()) {
            <a class="vx-ent-page-header__back" [routerLink]="backPath()" [queryParams]="backQuery() || {}">
              {{ backLabel() || 'Atrás' }}
            </a>
          } @else {
            <span></span>
          }
          @if (badge()) {
            <span class="vx-ent-page-header__badge" data-testid="report-kind-badge">{{ badge() }}</span>
          }
        </div>
      }
      <div class="vx-ent-page-header__copy">
        <h1 class="vx-ent-page-header__title">{{ title() }}</h1>
        @if (subtitle()) {
          <p class="vx-ent-page-header__lede">{{ subtitle() }}</p>
        }
      </div>
      @if (!reportMode() && (orgName() || (!backPath() && badge()))) {
        <div class="vx-hero__meta">
          @if (orgName()) {
            <span class="badge badge--active">{{ orgName() }}</span>
          }
        </div>
      }
      <div class="vx-ent-page-header__actions">
        <ng-content />
      </div>
    </header>
  `,
  styles: [
    `
      .vx-ent-page-header {
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
        margin-bottom: 1rem;
      }
      .vx-ent-page-header__nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        min-height: 1.25rem;
      }
      .vx-ent-page-header__back {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--vx-text-secondary, #8a8a8a);
        text-decoration: none;
      }
      .vx-ent-page-header__back:hover {
        color: var(--vx-accent, #1ed896);
        text-decoration: underline;
      }
      .vx-ent-page-header__badge {
        font-size: 0.625rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(138, 138, 138, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        padding: 0.15rem 0.5rem;
      }
      .vx-ent-page-header__title {
        margin: 0;
        font-size: clamp(1.35rem, 2.2vw, 1.75rem);
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.2;
        color: var(--vx-text, #e8e8e8);
      }
      .vx-ent-page-header__lede {
        margin: 0.35rem 0 0;
        font-size: 0.875rem;
        line-height: 1.45;
        color: var(--vx-text-secondary, #8a8a8a);
        max-width: 42rem;
      }
      .vx-ent-page-header__actions {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
      }
    `,
  ],
})
export class EnterprisePageHeaderComponent {
  readonly title = input.required<string>();
  readonly subtitle = input<string | undefined>();
  readonly orgName = input<string | undefined>();
  readonly badge = input<string | undefined>();
  readonly backPath = input<string | undefined>();
  readonly backLabel = input<string | undefined>();
  readonly backQuery = input<Record<string, string> | undefined>();
  /** Compact Reports detail chrome (back + quiet badge). */
  readonly reportMode = input(false);
}
