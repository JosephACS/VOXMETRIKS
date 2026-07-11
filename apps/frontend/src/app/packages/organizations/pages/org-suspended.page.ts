import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-org-suspended-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-suspended">
      <h1>Organización suspendida o acceso revocado</h1>
      <p class="lede">
        El contexto empresarial no está operativo. Las funciones personales siguen disponibles.
      </p>
      <div class="org-actions">
        <a class="org-btn org-btn--ghost" routerLink="/organizations/none">Ver estado</a>
        <a class="org-btn org-btn--ghost" routerLink="/discover">Modo personal</a>
      </div>
    </section>
  `,
})
export class OrgSuspendedPageComponent {}
