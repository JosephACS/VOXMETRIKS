import { Routes } from '@angular/router';
import { DashboardLayoutComponent } from './layouts/dashboard-layout/dashboard-layout.component';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { ProfilesLayoutComponent } from './layouts/profiles-layout/profiles-layout.component';
import { authGuard, guestGuard, roleHomeRedirectGuard } from './core/guards/auth.guard';
import { engineerGuard } from './core/guards/engineer.guard';
import { staffCapabilityGuard } from './core/guards/staff-capability.guard';
import {
  withProductSurfaceGuard,
} from './core/guards/with-product-surface-guard';
import { ORGANIZATIONS_ROUTES } from './packages/organizations/organizations.routes';
import { CRM_ROUTES } from './packages/crm/crm.routes';
import { SUBSCRIPTIONS_ROUTES } from './packages/subscriptions/subscriptions.routes';
import { BILLING_ROUTES } from './packages/billing/billing.routes';
import { ROYALTIES_ROUTES } from './packages/royalties/royalties.routes';
import { ARTIST_PROFILES_ROUTES } from './packages/artists/artists.routes';
import { CATALOG_RIGHTS_ROUTES } from './packages/catalog-rights/catalog-rights.routes';
import { CATALOG_PUBLISHING_ROUTES } from './packages/catalog-publishing/catalog-publishing.routes';
import { CAMPAIGNS_ROUTES } from './packages/campaigns/campaigns.routes';
import { BUSINESS_ANALYTICS_ROUTES } from './packages/business-analytics/business-analytics.routes';
import { COMPLIANCE_ROUTES } from './packages/compliance/compliance.routes';
import { PLATFORM_OPS_ROUTES } from './packages/platform-ops/platform-ops.routes';
import { ARTIST_SPACE_ROUTES } from './packages/artist-space/artist-space.routes';
import { REPORTING_ROUTES } from './packages/reporting/reporting.routes';
import { SIMPLE_REPORTS_ROUTES } from './packages/simple-reports/simple-reports.routes';
import { WORKPANEL_ROUTES } from './packages/workpanel/workpanel.routes';
import { COMPLEX_REPORTS_ROUTES } from './packages/complex-reports/complex-reports.routes';
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
    path: 'account/profiles',
    component: ProfilesLayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        title: 'personal.profiles.title',
        loadComponent: () =>
          import('./packages/personal-account/pages/profile-selector.page').then(
            (m) => m.ProfileSelectorPage,
          ),
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
        pathMatch: 'full',
        canActivate: [roleHomeRedirectGuard],
        loadComponent: () =>
          import('./core/guards/role-home-redirect.component').then(
            (m) => m.RoleHomeRedirectComponent,
          ),
      },
      {
        path: 'dashboard',
        redirectTo: 'workpanel',
        pathMatch: 'full',
      },
      {
        path: 'welcome',
        title: 'firstAccess.title',
        loadComponent: () =>
          import('./packages/personal-account/pages/first-access.page').then(
            (m) => m.FirstAccessPage,
          ),
      },
      {
        path: 'welcome/spaces',
        title: 'spaceChooser.title',
        loadComponent: () =>
          import('./core/spaces/pages/space-chooser.page').then((m) => m.SpaceChooserPage),
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
        redirectTo: 'workpanel',
        pathMatch: 'full',
      },
      {
        path: 'insights/tracks',
        redirectTo: 'complex-reports',
        pathMatch: 'full',
      },
      {
        path: 'insights/users',
        redirectTo: '/users',
        pathMatch: 'full',
      },
      {
        path: 'dashboard/analytics',
        redirectTo: 'workpanel',
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
        path: 'playlists/catalog/:id',
        title: 'playlists.catalogDetail',
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
        path: 'activity',
        title: 'activity.title',
        loadComponent: () =>
          import('./packages/streaming/activity/activity.page').then(
            (m) => m.ActivityPageComponent
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
        redirectTo: 'discover',
        pathMatch: 'full',
      },
      {
        path: 'analytics',
        redirectTo: 'workpanel',
        pathMatch: 'full',
      },
      {
        path: 'elt-pipeline',
        title: 'elt.title',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./packages/data-engineering/elt-pipeline/elt-pipeline.component').then(
            (m) => m.EltPipelineComponent,
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
            (m) => m.ExplorerComponent,
          ),
      },
      {
        path: 'comparatives',
        redirectTo: 'complex-reports',
        pathMatch: 'full',
      },
      {
        path: 'recommendations',
        title: 'nav.recommendations',
        loadComponent: () =>
          import('./packages/recommendations/recommendations.component').then(
            (m) => m.RecommendationsComponent,
          ),
      },
      {
        path: 'users',
        title: 'shell.myProfile',
        loadComponent: () =>
          import('./packages/users/users.component').then(
            (m) => m.UsersComponent,
          ),
      },
      {
        path: 'settings',
        title: 'nav.settings',
        loadComponent: () =>
          import('./packages/administration/settings/settings.component').then(
            (m) => m.SettingsComponent,
          ),
      },
      ...ORGANIZATIONS_ROUTES,
      ...withProductSurfaceGuard(CRM_ROUTES),
      ...withProductSurfaceGuard(SUBSCRIPTIONS_ROUTES),
      ...withProductSurfaceGuard(BILLING_ROUTES),
      ...withProductSurfaceGuard(ROYALTIES_ROUTES),
      ...ARTIST_PROFILES_ROUTES,
      ...CATALOG_RIGHTS_ROUTES,
      ...CATALOG_PUBLISHING_ROUTES,
      ...withProductSurfaceGuard(CAMPAIGNS_ROUTES),
      ...withProductSurfaceGuard(BUSINESS_ANALYTICS_ROUTES),
      ...withProductSurfaceGuard(COMPLIANCE_ROUTES),
      ...PLATFORM_OPS_ROUTES,
      ...ARTIST_SPACE_ROUTES,
      ...withProductSurfaceGuard(REPORTING_ROUTES),
      ...SIMPLE_REPORTS_ROUTES,
      ...WORKPANEL_ROUTES,
      ...COMPLEX_REPORTS_ROUTES,
      ...withProductSurfaceGuard(CUSTOMER_SUCCESS_ROUTES),
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
        path: 'error/module-unavailable',
        title: 'errors.moduleUnavailable.title',
        loadComponent: () =>
          import('./pages/module-unavailable/module-unavailable.page').then(
            (m) => m.ModuleUnavailablePageComponent,
          ),
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
    redirectTo: 'login',
  },
];

export const routes = APP_ROUTES;
