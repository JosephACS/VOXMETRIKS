import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

/**
 * Spec 038 — modules that exist technically but are outside the product-final surface.
 */
@Component({
  selector: 'app-module-unavailable-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="unavailable" role="status">
      <h1>Función no disponible</h1>
      <p>
        Esta función no está disponible en la versión actual de VOXMETRIKS.
      </p>
      <p class="muted">
        Puede formar parte de demos o capacidades futuras, pero no del producto final entregable.
      </p>
      <div class="actions">
        <a routerLink="/discover" class="btn">Ir a Discover</a>
        <a routerLink="/workpanel" class="btn btn--secondary">Ir a Workpanel</a>
        <a routerLink="/activity" class="btn btn--secondary">Tu actividad</a>
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
export class ModuleUnavailablePageComponent {}
