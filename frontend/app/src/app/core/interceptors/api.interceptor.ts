import {
  HttpErrorResponse,
  HttpInterceptorFn,
} from '@angular/common/http';
import {
  inject,
} from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Interceptor funcional — Agrega headers y maneja errores globales
 */
export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Obtener token actual
  const token = authService.getToken();

  // Clonar request y agregar headers
  let clonedReq = req.clone({
    setHeaders: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });

  // Agregar token si existe
  if (token) {
    clonedReq = clonedReq.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(clonedReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Logout si el servidor devuelve 401
      if (error.status === 401) {
        authService.logout();
        router.navigate(['/login']);
      }

      // Re-lanzar error para que los componentes lo manejen
      return throwError(() => error);
    })
  );
};
