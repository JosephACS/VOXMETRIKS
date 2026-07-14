import { Routes } from '@angular/router';
import { DashboardLayoutComponent } from './layouts/dashboard-layout/dashboard-layout.component';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { authGuard, guestGuard } from './core/guards/auth.guard';
import { engineerGuard } from './core/guards/engineer.guard';
import { ORGANIZATIONS_ROUTES } from './packages/organizations/organizations.routes';
import { CRM_ROUTES } from './packages/crm/crm.routes';
import { SUBSCRIPTIONS_ROUTES } from './packages/subscriptions/subscriptions.routes';
import { BILLING_ROUTES } from './packages/billing/billing.routes';
import { ARTIST_PROFILES_ROUTES } from './packages/artists/artists.routes';
import { CATALOG_RIGHTS_ROUTES } from './packages/catalog-rights/catalog-rights.routes';
import { CAMPAIGNS_ROUTES } from './packages/campaigns/campaigns.routes';
import { BUSINESS_ANALYTICS_ROUTES } from './packages/business-analytics/business-analytics.routes';
import { COMPLIANCE_ROUTES } from './packages/compliance/compliance.routes';
import { PLATFORM_OPS_ROUTES } from './packages/platform-ops/platform-ops.routes';
import { REPORTING_ROUTES } from './packages/reporting/reporting.routes';
import { CUSTOMER_SUCCESS_ROUTES } from './packages/customer-success/customer-success.routes';
import { PERSONAL_ACCOUNT_ROUTES } from './packages/personal-account/personal-account.routes';

export const APP_ROUTES: Routes = [
  {
    path: 'login',
    component: AuthLayoutComponent,
    canActivate: [guestGuard],
    children: [
      {
        path: '',
        title: 'login.title',
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
        redirectTo: 'discover',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        title: 'nav.analyticsHub',
        loadComponent: () =>
          import('./packages/analytics/dashboard/dashboard.component').then(
            (m) => m.DashboardComponent,
          ),
      },
      {
        path: 'discover',
        title: 'nav.home',
        loadComponent: () =>
          import('./packages/streaming/home/home.component').then(
            (m) => m.HomeComponent,
          ),
      },
      {
        path: 'insights/analytics',
        title: 'nav.streamsAnalytics',
        loadComponent: () =>
          import('./packages/analytics/stream-insights/analytics.component').then(
            (m) => m.AnalyticsFeatureComponent,
          ),
      },
      {
        path: 'insights/tracks',
        title: 'nav.topTracks',
        loadComponent: () =>
          import('./packages/analytics/top-tracks/tracks.component').then(
            (m) => m.TracksFeatureComponent,
          ),
      },
      {
        path: 'insights/users',
        redirectTo: '/users',
        pathMatch: 'full',
      },
      {
        path: 'dashboard/analytics',
        redirectTo: '/analytics',
        pathMatch: 'full',
      },
      {
        path: 'artists/:id',
        title: 'artistDetail.type',
        loadComponent: () =>
          import('./packages/streaming/artist-detail/artist-detail.component').then(
            (m) => m.ArtistDetailComponent
          ),
      },
      {
        path: 'artists',
        title: 'nav.artists',
        loadComponent: () =>
          import('./packages/streaming/artists/artists.component').then(
            (m) => m.ArtistsComponent
          ),
      },
      {
        path: 'tracks/:id',
        title: 'trackDetail.type',
        loadComponent: () =>
          import('./packages/streaming/track-detail/track-detail.component').then(
            (m) => m.TrackDetailComponent
          ),
      },
      {
        path: 'tracks',
        title: 'tracks.title',
        loadComponent: () =>
          import('./packages/streaming/tracks/tracks.component').then(
            (m) => m.TracksComponent
          ),
      },
      {
        path: 'search',
        title: 'nav.search',
        loadComponent: () =>
          import('./packages/streaming/search/search.component').then(
            (m) => m.SearchComponent
          ),
      },
      {
        path: 'playlists',
        title: 'playlists.title',
        loadComponent: () =>
          import('./packages/streaming/playlists/playlists.component').then(
            (m) => m.PlaylistsComponent
          ),
      },
      {
        path: 'playlists/:id',
        title: 'playlists.shareable',
        loadComponent: () =>
          import('./packages/streaming/playlists/playlists.component').then(
            (m) => m.PlaylistsComponent
          ),
      },
      {
        path: 'liked',
        title: 'liked.title',
        loadComponent: () =>
          import('./packages/streaming/liked/liked.component').then(
            (m) => m.LikedComponent
          ),
      },
      {
        path: 'history',
        title: 'nav.history',
        loadComponent: () =>
          import('./packages/history/history.component').then(
            (m) => m.HistoryComponent
          ),
      },
      {
        path: 'genres',
        title: 'nav.genres',
        loadComponent: () =>
          import('./packages/streaming/genres/genres.component').then(
            (m) => m.GenresComponent
          ),
      },
      {
        path: 'audio-features',
        title: 'nav.audioFeatures',
        loadComponent: () =>
          import('./packages/streaming/audio-features/audio-features.component').then(
            (m) => m.AudioFeaturesComponent
          ),
      },
      {
        path: 'trending',
        title: 'nav.trending',
        loadComponent: () =>
          import('./packages/analytics/trending/trending.component').then(
            (m) => m.TrendingComponent
          ),
      },
      {
        path: 'analytics',
        title: 'nav.analytics',
        loadComponent: () =>
          import('./packages/analytics/analytics/analytics.component').then(
            (m) => m.AnalyticsComponent
          ),
      },
      {
        path: 'elt-pipeline',
        title: 'elt.title',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./packages/data-engineering/elt-pipeline/elt-pipeline.component').then(
            (m) => m.EltPipelineComponent
          ),
      },
      {
        path: 'etl-pipeline',
        redirectTo: 'elt-pipeline',
        pathMatch: 'full',
      },
      {
        path: 'explorer',
        title: 'explorer.title',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./packages/data-engineering/explorer/explorer.component').then(
            (m) => m.ExplorerComponent
          ),
      },
      {
        path: 'comparatives',
        title: 'nav.comparatives',
        loadComponent: () =>
          import('./packages/analytics/comparatives/comparatives.component').then(
            (m) => m.ComparativesComponent
          ),
      },
      {
        path: 'recommendations',
        title: 'nav.recommendations',
        loadComponent: () =>
          import('./packages/recommendations/recommendations.component').then(
            (m) => m.RecommendationsComponent
          ),
      },
      {
        path: 'users',
        title: 'shell.myProfile',
        loadComponent: () =>
          import('./packages/users/users.component').then(
            (m) => m.UsersComponent
          ),
      },
      {
        path: 'settings',
        title: 'nav.settings',
        loadComponent: () =>
          import('./packages/administration/settings/settings.component').then(
            (m) => m.SettingsComponent
          ),
      },
      ...ORGANIZATIONS_ROUTES,
      ...CRM_ROUTES,
      ...SUBSCRIPTIONS_ROUTES,
      ...BILLING_ROUTES,
      ...ARTIST_PROFILES_ROUTES,
      ...CATALOG_RIGHTS_ROUTES,
      ...CAMPAIGNS_ROUTES,
      ...BUSINESS_ANALYTICS_ROUTES,
      ...COMPLIANCE_ROUTES,
      ...PLATFORM_OPS_ROUTES,
      ...REPORTING_ROUTES,
      ...CUSTOMER_SUCCESS_ROUTES,
      ...PERSONAL_ACCOUNT_ROUTES,
      {
        path: 'error/401',
        title: 'errors.401.title',
        loadComponent: () =>
          import('./pages/http-errors/http-error.pages').then((m) => m.Error401PageComponent),
      },
      {
        path: 'error/403',
        title: 'errors.403.title',
        loadComponent: () =>
          import('./pages/http-errors/http-error.pages').then((m) => m.Error403PageComponent),
      },
      {
        path: 'error/500',
        title: 'errors.500.title',
        loadComponent: () =>
          import('./pages/http-errors/http-error.pages').then((m) => m.Error500PageComponent),
      },
      {
        path: '**',
        title: 'notFound.title',
        loadComponent: () =>
          import('./pages/not-found/not-found.component').then(
            (m) => m.NotFoundComponent
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'discover',
  },
];

export const routes = APP_ROUTES;
