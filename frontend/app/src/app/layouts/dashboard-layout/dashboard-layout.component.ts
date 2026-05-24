import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { LoadingService } from '../../core/services/loading.service';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';

/**
 * Dashboard Layout Component
 * 
 * Layout principal para rutas protegidas (/dashboard/*)
 * Estructura:
 * - Topbar: Logo, breadcrumb, usuario + logout
 * - Sidebar: Navegación principal (colapsible en móvil)
 * - Main: Contenido dinámico (router-outlet)
 * - Global loading spinner: Mostrado cuando hay requests HTTP
 * 
 * Uso: Contenedor raíz para rutas /dashboard/overview, /dashboard/artists, etc.
 */
@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterOutlet,
    LoadingSpinnerComponent,
  ],
  templateUrl: './dashboard-layout.component.html',
  styleUrl: './dashboard-layout.component.css',
})
export class DashboardLayoutComponent implements OnInit {
  private readonly authService = inject(AuthService);
  protected readonly loadingService = inject(LoadingService);
  private readonly router = inject(Router);

  // Estado del sidebar (colapsado en móvil)
  protected sidebarCollapsed = signal(false);

  // Nombre de usuario
  protected userName = signal('User');

  // Rutas de navegación
  protected readonly navItems = [
    { label: 'Overview', path: '/dashboard/overview', icon: '📊' },
    { label: 'Artists', path: '/dashboard/artists', icon: '👥' },
    { label: 'Tracks', path: '/dashboard/tracks', icon: '🎵' },
    { label: 'Genres', path: '/dashboard/genres', icon: '🎸' },
  ];

  ngOnInit(): void {
    // Obtener nombre de usuario desde AuthService
    const user = this.authService.getUser();
    if (user?.username) {
      this.userName.set(user.username);
    }
  }

  /**
   * Toggle sidebar en móvil
   */
  protected toggleSidebar(): void {
    this.sidebarCollapsed.update((v) => !v);
  }

  /**
   * Cerrar sesión y redirigir a login
   */
  protected logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  /**
   * Cerrar sidebar al navegar (útil en móvil)
   */
  protected closeSidebarOnNav(): void {
    if (this.sidebarCollapsed()) {
      this.sidebarCollapsed.set(false);
    }
  }
}
