import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';

@Component({
  selector: 'app-org-none-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-none-page">
      <h1>Sin organización empresarial</h1>
      <p class="lede">
        Tu cuenta personal y las funciones demo siguen disponibles. Las rutas empresariales
        requieren una organización activa. No se crea ninguna organización automáticamente.
      </p>
      <div class="org-card">
        <p>Puedes crear una organización o aceptar una invitación si te enviaron un enlace.</p>
        <div class="org-actions">
          <a class="org-btn" routerLink="/organizations/new">Crear organización</a>
          <a class="org-btn org-btn--ghost" routerLink="/invitations/accept">Aceptar invitación</a>
          <a class="org-btn org-btn--ghost" routerLink="/discover">Seguir en modo personal</a>
        </div>
      </div>
      @if (ctx.organizations().length) {
        <div class="org-card">
          <h2>Organizaciones accesibles</h2>
          <ul>
            @for (o of ctx.organizations(); track o.id) {
              <li>
                {{ o.display_name }}
                <span class="org-badge" [class.org-badge--suspended]="o.status !== 'active'">{{ o.status }}</span>
              </li>
            }
          </ul>
        </div>
      }
    </section>
  `,
})
export class OrgNonePageComponent implements OnInit {
  readonly ctx = inject(OrganizationContextService);

  ngOnInit(): void {
    if (this.ctx.status() === 'idle') void this.ctx.bootstrap();
  }
}
