import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class LoadingService {
  // Signal que controla el estado global de carga
  private loadingCount = signal(0);

  // Signal reactivo público
  isLoading = () => this.loadingCount() > 0;

  /**
   * Incrementar contador de requests en progreso
   */
  startLoading(): void {
    this.loadingCount.update((count) => count + 1);
  }

  /**
   * Decrementar contador de requests en progreso
   */
  stopLoading(): void {
    this.loadingCount.update((count) => Math.max(0, count - 1));
  }

  /**
   * Resetear contador (para casos excepcionales)
   */
  reset(): void {
    this.loadingCount.set(0);
  }
}
