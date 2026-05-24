/**
 * app.config.ts
 * =============
 * Configuración raíz de la aplicación Angular standalone.
 * Registra: Router, HttpClient + interceptors, animaciones.
 */

import {
  ApplicationConfig,
  provideZoneChangeDetection,
} from '@angular/core';
import {
  provideRouter,
  withComponentInputBinding,
} from '@angular/router';
import {
  provideHttpClient,
  withInterceptors,
  withFetch,
} from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';

import { routes }             from './app.routes';
import { apiInterceptor }     from './core/interceptors/api.interceptor';
import { loadingInterceptor } from './core/interceptors/loading.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // Detección de cambios optimizada
    provideZoneChangeDetection({ eventCoalescing: true }),

    // Router con input binding
    provideRouter(routes, withComponentInputBinding()),

    // HttpClient con Fetch API + interceptors funcionales
    provideHttpClient(
      withFetch(),
      withInterceptors([loadingInterceptor, apiInterceptor])
    ),

    // Animaciones para transiciones de layout
    provideAnimations(),
  ],
};
