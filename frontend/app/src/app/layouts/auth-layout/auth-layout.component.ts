import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';

/**
 * Auth Layout Component
 * 
 * Layout para páginas de autenticación (login, registro, etc.)
 * - Página centrada
 * - Sin sidebar ni topbar
 * - Fondo oscuro minimalista
 * - Branding VOXMETRIK
 * 
 * Uso: Contenedor raíz para rutas /login, /register, /forgot-password, etc.
 */
@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './auth-layout.component.html',
  styleUrl: './auth-layout.component.css',
})
export class AuthLayoutComponent {
  // No hay lógica adicional — solo es un contenedor visual
}
