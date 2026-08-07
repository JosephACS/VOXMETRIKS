import { productSurfaceGuard } from './product-surface.guard';
import { prependRouteGuard } from './product-surface.routes';
import type { Routes } from '@angular/router';

/** Spec 038 — wrap demo packages with productSurfaceGuard. */
export function withProductSurfaceGuard(routes: Routes): Routes {
  return prependRouteGuard(routes, productSurfaceGuard);
}
