import { HttpInterceptorFn } from '@angular/common/http';
import { inject }            from '@angular/core';
import { finalize }          from 'rxjs';
import { LoadingService }    from '../../shared/services/loading.service';

/**
 * loadingInterceptor — barra superior de progreso (no overlay de pantalla completa).
 * Ignora fuentes y peticiones estáticas para no parpadear al navegar entre módulos.
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  if (
    req.url.startsWith('https://fonts.') ||
    req.url.startsWith('chrome-extension') ||
    req.url.includes('/assets/')
  ) {
    return next(req);
  }

  const loading = inject(LoadingService);
  loading.startLoading();

  return next(req).pipe(
    finalize(() => loading.stopLoading()),
  );
};
