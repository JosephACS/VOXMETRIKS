import { Routes } from '@angular/router';

export const artistsRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./artists.component').then(m => m.ArtistsComponent),
  },
];
