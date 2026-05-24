import { HttpInterceptorFn } from '@angular/common/http';
import { inject }            from '@angular/core';
import { finalize }          from 'rxjs';
import { LoadingService }    from '../../shared/services/loading.service';

/**
 * loadingInterceptor — interceptor funcional para loading global.
 * Usa el LoadingService de shared (tiene isLoading$ para el spinner).
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.url.startsWith('https://fonts.') || req.url.startsWith('chrome-extension')) {
    return next(req);
  }

  const loading = inject(LoadingService);
  loading.startLoading();

  return next(req).pipe(
    finalize(() => loading.stopLoading()),
  );
};
