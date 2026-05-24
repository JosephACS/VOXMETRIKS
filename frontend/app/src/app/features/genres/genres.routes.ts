import { Routes } from '@angular/router';

export const genresRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./genres.component').then(m => m.GenresComponent),
  },
];
