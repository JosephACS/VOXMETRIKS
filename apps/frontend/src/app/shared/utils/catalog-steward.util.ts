import { inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

/** Block catalog steward actions unless logged in as admin (Spotify-like: listeners don't edit catalog). */
export function assertCatalogSteward(auth = inject(AuthService)): void {
  if (!auth.isCatalogSteward()) {
    throw new Error('Solo el administrador puede modificar el catálogo musical.');
  }
}
