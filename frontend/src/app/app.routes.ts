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
          import('./packages/analytics/dashboard/dashboard.component').then(
            (m) => m.DashboardComponent
          ),
      },
      {
        path: 'artists',
        loadComponent: () =>
          import('./packages/streaming/artists/artists.component').then(
            (m) => m.ArtistsComponent
          ),
      },
      {
        path: 'tracks',
        loadComponent: () =>
          import('./packages/streaming/tracks/tracks.component').then(
            (m) => m.TracksComponent
          ),
      },
      {
        path: 'genres',
        loadComponent: () =>
          import('./packages/streaming/genres/genres.component').then(
            (m) => m.GenresComponent
          ),
      },
      {
        path: 'audio-features',
        loadComponent: () =>
          import('./packages/streaming/audio-features/audio-features.component').then(
            (m) => m.AudioFeaturesComponent
          ),
      },
      {
        path: 'trending',
        loadComponent: () =>
          import('./packages/analytics/trending/trending.component').then(
            (m) => m.TrendingComponent
          ),
      },
      {
        path: 'analytics',
        loadComponent: () =>
          import('./packages/analytics/analytics/analytics.component').then(
            (m) => m.AnalyticsComponent
          ),
      },
      {
        path: 'etl-pipeline',
        loadComponent: () =>
          import('./packages/data-engineering/etl-pipeline/etl-pipeline.component').then(
            (m) => m.EtlPipelineComponent
          ),
      },
      {
        path: 'explorer',
        loadComponent: () =>
          import('./packages/data-engineering/explorer/explorer.component').then(
            (m) => m.ExplorerComponent
          ),
      },
      {
        path: 'comparatives',
        loadComponent: () =>
          import('./packages/analytics/comparatives/comparatives.component').then(
            (m) => m.ComparativesComponent
          ),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./packages/administration/settings/settings.component').then(
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
