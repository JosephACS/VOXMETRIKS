import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Loading Spinner Component
 * 
 * Indicador de carga reutilizable.
 * Puede usarse como spinner pequeño inline o como overlay fullpage.
 * 
 * Uso:
 * <app-loading-spinner />
 * <app-loading-spinner [fullpage]="true" label="Cargando..." />
 */
@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './loading-spinner.component.html',
  styleUrl: './loading-spinner.component.css',
})
export class LoadingSpinnerComponent {
  /**
   * Si es true, ocupa toda la pantalla con overlay semi-transparente
   * Si es false (default), es un spinner pequeño inline
   */
  @Input() fullpage: boolean = false;

  /**
   * Texto opcional a mostrar debajo del spinner
   */
  @Input() label: string | null = null;

  /**
   * Tamaño: 'sm' (24px), 'md' (40px), 'lg' (60px)
   */
  @Input() size: 'sm' | 'md' | 'lg' = 'md';

  /**
   * Clase CSS dinámica para tamaño
   */
  get sizeClass(): string {
    return `spinner-${this.size}`;
  }

  /**
   * Clase CSS dinámica para fullpage
   */
  get fullpageClass(): string {
    return this.fullpage ? 'spinner-fullpage' : 'spinner-inline';
  }
}
