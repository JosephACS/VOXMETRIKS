import { Component }  from '@angular/core';
import { RouterOutlet } from '@angular/router';

/**
 * AuthLayoutComponent — Shell para rutas públicas (login).
 * Sin sidebar ni topbar. Centra el contenido en pantalla completa.
 * Sin lógica adicional — solo contenedor visual.
 */
@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './auth-layout.component.html',
  styleUrl:    './auth-layout.component.css',
})
export class AuthLayoutComponent {}
