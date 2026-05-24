import { Routes } from '@angular/router';

export const tracksRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./tracks.component').then(m => m.TracksComponent),
  },
];
