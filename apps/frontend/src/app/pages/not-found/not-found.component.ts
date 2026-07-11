import { I18nService } from '../../core/services/i18n.service';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
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
        <a routerLink="/discover" class="btn btn-primary not-found-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          {{ 'notFound.back' | t:lang() }}
        </a>
      </div>
    </div>
  `,
  styles: [`
    .not-found-layout {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--color-bg);
      padding: 2rem;
    }

    .not-found-container {
      text-align: center;
      animation: fadeInUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) both;
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
  `],
})
export class NotFoundComponent {
  readonly lang = inject(I18nService).lang;}
