import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

function isCatalogStewardMutation(url: string, method: string): boolean {
  if (!['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) return false;
  const path = url.replace(/^https?:\/\/[^/]+/, '');
  return /\/api\/v1\/(artists|genres|tracks)(\/|\?|$)/.test(path);
}

/** Blocks catalog POST/PUT/DELETE for non-admin users (defense in depth vs UI leaks). */
export const catalogStewardInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  if (auth.isCatalogSteward() || !isCatalogStewardMutation(req.url, req.method)) {
    return next(req);
  }
  return throwError(
    () =>
      new HttpErrorResponse({
        status: 403,
        statusText: 'Forbidden',
        error: { detail: 'Solo el administrador puede modificar el catálogo musical.' },
        url: req.url,
      }),
  );
};
