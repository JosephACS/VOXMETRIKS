import { Component, inject, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { homePathForRole } from '../../core/navigation/nav-access.policy';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { SpaceContextService } from '../../core/spaces/space-context.service';
import { homePathForSpace } from '../../core/spaces/space.models';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-http-error',
  standalone: true,
  imports: [RouterLink, TranslatePipe],
  template: `
    <div class="http-error-layout">
      <div class="http-error-container">
        <div class="http-error-code" aria-hidden="true">{{ code }}</div>
        <h1 class="http-error-title">{{ titleKey | t:lang() }}</h1>
        <p class="http-error-body">{{ bodyKey | t:lang() }}</p>
        <a [routerLink]="resolvedCtaLink" class="btn btn-primary">{{ ctaKey | t:lang() }}</a>
      </div>
    </div>
  `,
  styles: [
    `
      .http-error-layout {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--color-bg, var(--vx-bg));
        padding: 2rem;
      }
      .http-error-container {
        text-align: center;
      }
      .http-error-code {
        font-family: var(--font-mono);
        font-size: clamp(4rem, 12vw, 6rem);
        font-weight: 300;
        color: var(--color-surface-3);
        line-height: 1;
        margin-bottom: 1.5rem;
      }
      .http-error-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--color-text);
        margin-bottom: 0.75rem;
      }
      .http-error-body {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-bottom: 2rem;
      }
    `,
  ],
})
export class HttpErrorPageComponent {
  private readonly auth = inject(AuthService);
  private readonly spaceCtx = inject(SpaceContextService);
  readonly lang = inject(I18nService).lang;

  @Input() code = '500';
  @Input() titleKey = 'errors.500.title';
  @Input() bodyKey = 'errors.500.body';
  @Input() ctaKey = 'errors.500.cta';
  /** When empty, CTA uses role home. */
  @Input() ctaLink = '';

  get resolvedCtaLink(): string {
    if (this.ctaLink) return this.ctaLink;
    if (!this.auth.isAuthenticated()) return '/login';
    const activeSpace = this.spaceCtx.activeSpace();
    if (activeSpace) return homePathForSpace(activeSpace);
    return homePathForRole(this.auth.role());
  }
}

@Component({
  selector: 'app-error-401',
  standalone: true,
  imports: [HttpErrorPageComponent],
  template: `<app-http-error
    code="401"
    titleKey="errors.401.title"
    bodyKey="errors.401.body"
    ctaKey="errors.401.cta"
    ctaLink="/login"
  />`,
})
export class Error401PageComponent {}

@Component({
  selector: 'app-error-403',
  standalone: true,
  imports: [HttpErrorPageComponent],
  template: `<app-http-error
    code="403"
    titleKey="errors.403.title"
    bodyKey="errors.403.body"
    ctaKey="errors.403.cta"
  />`,
})
export class Error403PageComponent {}

@Component({
  selector: 'app-error-500',
  standalone: true,
  imports: [HttpErrorPageComponent],
  template: `<app-http-error
    code="500"
    titleKey="errors.500.title"
    bodyKey="errors.500.body"
    ctaKey="errors.500.cta"
  />`,
})
export class Error500PageComponent {}
