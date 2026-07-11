import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-org-closed-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-closed">
      <h1>Organización cerrada o contexto inválido</h1>
      <p class="lede">
        Esta organización ya no está disponible para operaciones. Puedes cambiar de organización
        o continuar en modo personal.
      </p>
      <div class="org-actions">
        <a class="org-btn org-btn--ghost" routerLink="/organizations/none">Sin organización</a>
        <a class="org-btn org-btn--ghost" routerLink="/discover">Modo personal</a>
      </div>
    </section>
  `,
})
export class OrgClosedPageComponent {}
