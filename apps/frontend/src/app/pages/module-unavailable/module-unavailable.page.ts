import { Component, computed, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs/operators';
import { I18nService } from '../../core/services/i18n.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

/**
 * Spec 038 / 054 — product-surface denial landing.
 * Distinguishes space mismatch vs residual unavailable; plan-required usually
 * redirects to onboarding before reaching this page.
 */
@Component({
  selector: 'app-module-unavailable-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="unavailable" role="status" data-testid="module-unavailable">
      <h1>{{ titleKey() | t:lang() }}</h1>
      <p>{{ bodyKey() | t:lang() }}</p>
      <p class="muted">{{ hintKey() | t:lang() }}</p>
      <div class="actions">
        @if (reason() === 'plan') {
          <a routerLink="/subscriptions/select-plan" class="btn">
            {{ 'errors.moduleUnavailable.ctaPlan' | t:lang() }}
          </a>
          <a routerLink="/organizations" class="btn btn--secondary">
            {{ 'errors.moduleUnavailable.ctaOrg' | t:lang() }}
          </a>
        }
        <a routerLink="/discover" class="btn" [class.btn--secondary]="reason() === 'plan'">
          {{ 'errors.moduleUnavailable.ctaDiscover' | t:lang() }}
        </a>
        <a routerLink="/activity" class="btn btn--secondary">
          {{ 'errors.moduleUnavailable.ctaActivity' | t:lang() }}
        </a>
      </div>
    </div>
  `,
  styles: [
    `
      .unavailable {
        max-width: 36rem;
        margin: 3rem auto;
        padding: 1.5rem;
        text-align: center;
      }
      h1 {
        font-size: 1.5rem;
        margin-bottom: 0.75rem;
      }
      .muted {
        opacity: 0.75;
        font-size: 0.95rem;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        justify-content: center;
        margin-top: 1.5rem;
      }
      .btn {
        display: inline-block;
        padding: 0.55rem 1rem;
        border-radius: 0.4rem;
        background: var(--vx-accent, #1a7a4c);
        color: #fff;
        text-decoration: none;
      }
      .btn--secondary {
        background: transparent;
        border: 1px solid currentColor;
        color: inherit;
      }
    `,
  ],
})
export class ModuleUnavailablePageComponent {
  private readonly i18n = inject(I18nService);
  private readonly route = inject(ActivatedRoute);
  readonly lang = this.i18n.lang;

  private readonly query = toSignal(
    this.route.queryParamMap.pipe(
      map((p) => ({
        reason: (p.get('reason') || 'unavailable').toLowerCase(),
      })),
    ),
    { initialValue: { reason: 'unavailable' } },
  );

  readonly reason = computed(() => this.query().reason);

  readonly titleKey = computed(() =>
    this.reason() === 'plan'
      ? 'errors.moduleUnavailable.planTitle'
      : this.reason() === 'space'
        ? 'errors.moduleUnavailable.spaceTitle'
        : 'errors.moduleUnavailable.title',
  );

  readonly bodyKey = computed(() =>
    this.reason() === 'plan'
      ? 'errors.moduleUnavailable.planBody'
      : this.reason() === 'space'
        ? 'errors.moduleUnavailable.spaceBody'
        : 'errors.moduleUnavailable.body',
  );

  readonly hintKey = computed(() =>
    this.reason() === 'plan'
      ? 'errors.moduleUnavailable.planHint'
      : 'errors.moduleUnavailable.hint',
  );
}
