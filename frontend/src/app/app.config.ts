/**
 * app.config.ts — Configuración raíz de la aplicación Angular standalone.
 *
 * Providers registrados:
 * - Router con lazy loading + title strategy + input binding
 * - HttpClient con Fetch API + interceptors funcionales
 * - Animaciones para transiciones de layout
 */

import {
  ApplicationConfig,
  provideZoneChangeDetection,
} from '@angular/core';
import {
  provideRouter,
  withComponentInputBinding,
  withInMemoryScrolling,
  TitleStrategy,
} from '@angular/router';
import {
  provideHttpClient,
  withInterceptors,
  withFetch,
} from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { APP_ROUTES as routes } from './app.routes';
import { apiInterceptor }     from './core/interceptors/api.interceptor';
import { loadingInterceptor } from './core/interceptors/loading.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // Optimización de detección de cambios
    provideZoneChangeDetection({ eventCoalescing: true }),

    // Router: lazy loading, scroll restaurado, input binding
    provideRouter(
      routes,
      withComponentInputBinding(),
      withInMemoryScrolling({
        scrollPositionRestoration: 'top',
        anchorScrolling: 'enabled',
      }),
    ),

    // HttpClient: Fetch API nativa + interceptors funcionales
    provideHttpClient(
      withFetch(),
      withInterceptors([loadingInterceptor, apiInterceptor]),
    ),

    // Animaciones asíncronas (no bloquean bootstrap)
    provideAnimationsAsync(),
  ],
};
