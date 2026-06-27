import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/** On 401 from protected API routes, clear stale client session and send to login. */
export const authErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const isApi = req.url.includes('/api/v1');
      const isAuthRoute =
        req.url.includes('/users/login') ||
        req.url.includes('/users/register') ||
        req.url.includes('/users/verify-email') ||
        req.url.includes('/users/resend-code') ||
        req.url.includes('/users/google') ||
        req.url.includes('/users/auth-config');
      if (err.status === 401 && isApi && !isAuthRoute) {
        auth.clearSession();
        void router.navigate(['/login']);
      }
      return throwError(() => err);
    }),
  );
};
