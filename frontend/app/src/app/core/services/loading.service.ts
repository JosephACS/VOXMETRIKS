import { Injectable, signal, computed } from '@angular/core';

/**
 * LoadingService — estado global de carga HTTP.
 *
 * Usa un contador de requests activos en lugar de un booleano simple,
 * para manejar correctamente múltiples requests paralelos (forkJoin).
 *
 * Consumido por:
 * - loadingInterceptor: llama startLoading/stopLoading por cada request
 * - DashboardLayoutComponent: muestra global loading bar
 */
@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly _count = signal(0);

  /** true si hay al menos un request activo */
  readonly isLoading = computed(() => this._count() > 0);

  startLoading(): void {
    this._count.update(n => n + 1);
  }

  stopLoading(): void {
    this._count.update(n => Math.max(0, n - 1));
  }

  reset(): void {
    this._count.set(0);
  }
}
