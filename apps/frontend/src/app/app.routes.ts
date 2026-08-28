import { Routes } from '@angular/router';
import { authGuard, guestGuard, roleHomeRedirectGuard } from './core/guards/auth.guard';
import { engineerGuard } from './core/guards/engineer.guard';

export const APP_ROUTES: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./layouts/auth-layout/auth-layout.component').then(
        (m) => m.AuthLayoutComponent,
      ),
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
    loadComponent: () =>
      import('./layouts/profiles-layout/profiles-layout.component').then(
        (m) => m.ProfilesLayoutComponent,
      ),
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
    loadComponent: () =>
      import('./layouts/dashboard-layout/dashboard-layout.component').then(
        (m) => m.DashboardLayoutComponent,
      ),
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
        path: 'home',
        redirectTo: 'discover',
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
      {
        path: 'integrations/spotify/callback',
        title: 'Spotify | VOXMETRIKS',
        loadComponent: () =>
          import('./core/integrations/spotify/spotify-callback.page').then(
            (m) => m.SpotifyCallbackPage,
          ),
      },
      {
        path: '',
        loadChildren: () =>
          import('./app.product.routes').then((m) => m.PRODUCT_ROUTES),
      },
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
