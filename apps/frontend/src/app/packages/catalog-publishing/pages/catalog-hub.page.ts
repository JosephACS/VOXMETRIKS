import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

/**
 * Spec 043 — Catálogo y publicación hub.
 * Reuses existing routes via secondary nav; no duplicated business logic.
 */
@Component({
  selector: 'app-catalog-hub-page',
  standalone: true,
  imports: [CommonModule, RouterLink, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise catalog-hub">
      <app-enterprise-page-header
        title="Catálogo y publicación"
        subtitle="Gestione artistas, canciones, lanzamientos, revisiones y derechos."
      />

      <div class="hub-grid">
        @for (card of cards; track card.path) {
          <a class="hub-card" [routerLink]="card.path">
            <strong>{{ card.label }}</strong>
            <span>{{ card.hint }}</span>
          </a>
        }
      </div>
    </div>
  `,
  styles: [
    `
      .hub-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.75rem;
      }
      .hub-card {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        text-decoration: none;
        color: inherit;
        background: var(--color-surface, rgba(24, 24, 24, 0.92));
        border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.04));
        transition: background 120ms ease, border-color 120ms ease;
      }
      .hub-card:hover {
        background: var(--color-surface-2, rgba(32, 32, 32, 0.98));
        border-color: rgba(30, 216, 150, 0.28);
      }
      .hub-card strong {
        font-size: 0.9375rem;
      }
      .hub-card span {
        font-size: 0.8125rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
        line-height: 1.35;
      }
    `,
  ],
})
export class CatalogHubPage {
  private readonly orgCtx = inject(OrganizationContextService);

  readonly cards = [
    { path: '/artist-profiles', label: 'Artistas', hint: 'Perfiles y equipo artístico' },
    { path: '/artist/tracks', label: 'Canciones', hint: 'Catálogo de pistas publicables' },
    { path: '/artist/releases', label: 'Lanzamientos', hint: 'Borradores, revisión y publicados' },
    { path: '/artist/releases/new', label: 'Publicar música', hint: 'Asistente de nuevo lanzamiento' },
    { path: '/catalog-review', label: 'Revisiones', hint: 'Bandeja de observaciones' },
    { path: '/catalog-rights/assets', label: 'Catálogo musical', hint: 'Activos y metadatos' },
    { path: '/catalog-rights/conflicts', label: 'Derechos', hint: 'Contratos y conflictos' },
  ];

  constructor() {
    void this.orgCtx;
  }
}
