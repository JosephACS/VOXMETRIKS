import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-crm-access-denied-page',
  standalone: true,
  imports: [RouterLink],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-access-denied-page">
      <h1>Acceso CRM no autorizado</h1>
      <p class="lede">
        Tu cuenta no tiene ningún rol CRM asignado en esta plataforma.
        Contacta a un administrador para obtener acceso de <em>sales_agent</em> o <em>sales_manager</em>.
      </p>
      <div class="crm-card">
        <p>Si crees que esto es un error, cierra sesión y vuelve a iniciar.</p>
        <div class="crm-actions">
          <a class="crm-btn crm-btn--ghost" routerLink="/discover">Ir al inicio</a>
          <a class="crm-btn crm-btn--ghost" routerLink="/settings">Mi perfil</a>
        </div>
      </div>
    </section>
  `,
})
export class CrmAccessDeniedPageComponent {}
