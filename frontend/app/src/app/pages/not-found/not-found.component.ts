import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="nf-wrap">
      <div class="nf-code font-mono">404</div>
      <h1 class="nf-title">Página no encontrada</h1>
      <p class="nf-sub">La ruta que buscas no existe en el sistema.</p>
      <a routerLink="/dashboard" class="btn btn-primary">← Volver al dashboard</a>
    </div>
  `,
  styles: [`
    .nf-wrap {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      background: var(--color-bg);
      padding: 2rem;
      text-align: center;
    }
    .nf-code {
      font-size: 6rem;
      font-weight: 500;
      color: var(--color-border-hover);
      letter-spacing: -0.04em;
      line-height: 1;
    }
    .nf-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--color-text);
    }
    .nf-sub {
      font-size: 0.875rem;
      color: var(--color-text-muted);
      margin-bottom: 1rem;
    }
  `],
})
export class NotFoundComponent {}
