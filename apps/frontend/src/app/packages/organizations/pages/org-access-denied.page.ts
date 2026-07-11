import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-org-access-denied-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-access-denied">
      <h1>Acceso denegado</h1>
      <p class="lede">No tienes permiso para esta acción en la organización activa.</p>
      <div class="org-actions">
        <a class="org-btn org-btn--ghost" routerLink="/discover">Volver</a>
      </div>
    </section>
  `,
})
export class OrgAccessDeniedPageComponent {}
