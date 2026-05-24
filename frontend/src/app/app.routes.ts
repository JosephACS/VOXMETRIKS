import { Routes } from '@angular/router';
import { DashboardLayoutComponent } from './layouts/dashboard-layout/dashboard-layout.component';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { authGuard, guestGuard } from './core/guards/auth.guard';

export const APP_ROUTES: Routes = [
  {
    path: 'login',
    component: AuthLayoutComponent,
    canActivate: [guestGuard],
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pages/login/login.component').then((m) => m.LoginComponent),
      },
    ],
  },
  {
    path: '',
    component: DashboardLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./packages/streaming/home/home.component').then(
            (m) => m.HomeComponent
          ),
      },
      {
        path: 'dashboard/analytics',
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
        path: 'tracks/:id',
        loadComponent: () =>
          import('./packages/streaming/track-detail/track-detail.component').then(
            (m) => m.TrackDetailComponent
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
        path: 'search',
        loadComponent: () =>
          import('./packages/streaming/search/search.component').then(
            (m) => m.SearchComponent
          ),
      },
      {
        path: 'playlists',
        loadComponent: () =>
          import('./packages/streaming/playlists/playlists.component').then(
            (m) => m.PlaylistsComponent
          ),
      },
      {
        path: 'liked',
        loadComponent: () =>
          import('./packages/streaming/liked/liked.component').then(
            (m) => m.LikedComponent
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
        path: 'elt-pipeline',
        loadComponent: () =>
          import('./packages/data-engineering/etl-pipeline/etl-pipeline.component').then(
            (m) => m.EtlPipelineComponent
          ),
      },
      {
        path: 'etl-pipeline',
        redirectTo: 'elt-pipeline',
        pathMatch: 'full',
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
        path: 'recommendations',
        loadComponent: () =>
          import('./packages/recommendations/recommendations.component').then(
            (m) => m.RecommendationsComponent
          ),
      },
      {
        path: 'users',
        loadComponent: () =>
          import('./packages/users/users.component').then(
            (m) => m.UsersComponent
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

export const routes = APP_ROUTES;
