import {
  HttpInterceptorFn,
} from '@angular/common/http';
import {
  inject,
} from '@angular/core';
import { finalize } from 'rxjs';
import { LoadingService } from '../services/loading.service';

/**
 * Interceptor funcional — Maneja el estado global de loading
 */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loadingService = inject(LoadingService);

  // Iniciar loading
  loadingService.startLoading();

  // Finalizar loading cuando se complete (success o error)
  return next(req).pipe(
    finalize(() => loadingService.stopLoading())
  );
};
