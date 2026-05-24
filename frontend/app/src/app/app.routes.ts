import { Routes } from '@angular/router';
import { DashboardLayoutComponent } from './layouts/dashboard-layout/dashboard-layout.component';

export const APP_ROUTES: Routes = [
  {
    path: '',
    component: DashboardLayoutComponent,
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then(
            (m) => m.DashboardComponent
          ),
      },
      {
        path: 'artists',
        loadComponent: () =>
          import('./features/artists/artists.component').then(
            (m) => m.ArtistsComponent
          ),
      },
      {
        path: 'tracks',
        loadComponent: () =>
          import('./features/tracks/tracks.component').then(
            (m) => m.TracksComponent
          ),
      },
      {
        path: 'genres',
        loadComponent: () =>
          import('./features/genres/genres.component').then(
            (m) => m.GenresComponent
          ),
      },
      {
        path: 'audio-features',
        loadComponent: () =>
          import('./features/audio-features/audio-features.component').then(
            (m) => m.AudioFeaturesComponent
          ),
      },
      {
        path: 'trending',
        loadComponent: () =>
          import('./features/trending/trending.component').then(
            (m) => m.TrendingComponent
          ),
      },
      {
        path: 'analytics',
        loadComponent: () =>
          import('./features/analytics/analytics.component').then(
            (m) => m.AnalyticsComponent
          ),
      },
      {
        path: 'etl-pipeline',
        loadComponent: () =>
          import('./features/etl-pipeline/etl-pipeline.component').then(
            (m) => m.EtlPipelineComponent
          ),
      },
      {
        path: 'explorer',
        loadComponent: () =>
          import('./features/explorer/explorer.component').then(
            (m) => m.ExplorerComponent
          ),
      },
      {
        path: 'comparatives',
        loadComponent: () =>
          import('./features/comparatives/comparatives.component').then(
            (m) => m.ComparativesComponent
          ),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/settings/settings.component').then(
            (m) => m.SettingsComponent
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];

// Alias para compatibilidad con app.config.ts
export const routes = APP_ROUTES;
