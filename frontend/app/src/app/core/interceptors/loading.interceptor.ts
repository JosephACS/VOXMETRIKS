import { HttpInterceptorFn } from '@angular/common/http';
import { inject }            from '@angular/core';
import { finalize }          from 'rxjs';
import { LoadingService }    from '../services/loading.service';

/**
 * loadingInterceptor — interceptor funcional para loading global.
 * Activa LoadingService al inicio de cada request HTTP y lo desactiva
 * cuando el observable completa (success o error).
 *
 * Excluye requests a recursos estáticos y Google Fonts para evitar
 * falsos positivos en el loading bar.
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  // No activar loading para recursos externos
  if (req.url.startsWith('https://fonts.') || req.url.startsWith('chrome-extension')) {
    return next(req);
  }

  const loading = inject(LoadingService);
  loading.startLoading();

  return next(req).pipe(
    finalize(() => loading.stopLoading()),
  );
};
