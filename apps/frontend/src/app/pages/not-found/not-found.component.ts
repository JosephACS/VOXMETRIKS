import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { homePathForRole } from '../../core/navigation/nav-access.policy';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [RouterLink, TranslatePipe],
  template: `
    <div class="not-found-layout">
      <div class="not-found-container">
        <div class="not-found-code" aria-hidden="true">404</div>
        <h1 class="not-found-title">{{ 'notFound.title' | t:lang() }}</h1>
        <p class="not-found-body">{{ 'notFound.body' | t:lang() }}</p>
        <a [routerLink]="homeLink" class="btn btn-primary not-found-btn">
          {{ 'notFound.back' | t:lang() }}
        </a>
      </div>
    </div>
  `,
  styles: [
    `
      .not-found-layout {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--color-bg, var(--vx-bg));
        padding: 2rem;
      }
      .not-found-container {
        text-align: center;
      }
      .not-found-code {
        font-family: var(--font-mono);
        font-size: clamp(5rem, 15vw, 8rem);
        font-weight: 300;
        color: var(--color-surface-3);
        line-height: 1;
        letter-spacing: -0.05em;
        margin-bottom: 1.5rem;
        user-select: none;
      }
      .not-found-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--color-text);
        margin-bottom: 0.75rem;
      }
      .not-found-body {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-bottom: 2.5rem;
      }
      .not-found-btn {
        font-size: 0.875rem;
        padding: 0.625rem 1.25rem;
      }
    `,
  ],
})
export class NotFoundComponent {
  private readonly auth = inject(AuthService);
  readonly lang = inject(I18nService).lang;
  readonly homeLink = this.auth.isAuthenticated()
    ? homePathForRole(this.auth.role())
    : '/login';
}
