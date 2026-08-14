import { describe, expect, it } from 'vitest';
import { APP_ROUTES } from '../../app.routes';

describe('Phase C route stability (spec 014)', () => {
  const layout = APP_ROUTES.find((r) => r.path === '' && r.children);
  const children = layout?.children ?? [];

  function child(path: string) {
    return children.find((c) => c.path === path);
  }

  it('keeps required public paths', () => {
    for (const required of [
      'dashboard',
      'insights/analytics',
      'insights/tracks',
      'analytics',
      'trending',
      'comparatives',
      'tracks',
      'tracks/:id',
    ]) {
      expect(child(required)).toBeTruthy();
    }
  });

  it('keeps dashboard/insights as stable redirects into staff surfaces', () => {
    // Spec 037/044 recovery: legacy analytics entrypoints redirect to Workpanel / complex reports.
    expect(child('dashboard')?.redirectTo).toBe('workpanel');
    expect(child('insights/analytics')?.redirectTo).toBe('workpanel');
    expect(child('insights/tracks')?.redirectTo).toBe('complex-reports');
    expect(child('analytics')?.redirectTo).toBe('workpanel');
    // Trending is a listener-facing surface, so it folds into Discover, not reports.
    expect(child('trending')?.redirectTo).toBe('discover');
    expect(child('comparatives')?.redirectTo).toBe('complex-reports');
    expect(child('tracks')?.loadComponent).toBeTypeOf('function');
    expect(child('tracks/:id')?.loadComponent).toBeTypeOf('function');
  });
});
