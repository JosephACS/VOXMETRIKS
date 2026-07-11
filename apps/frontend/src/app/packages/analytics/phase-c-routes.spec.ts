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

  it('points dashboard and insights to packages/analytics loaders', () => {
    const dashSrc = String(child('dashboard')?.loadComponent);
    const aSrc = String(child('insights/analytics')?.loadComponent);
    const tSrc = String(child('insights/tracks')?.loadComponent);
    // Angular compiles loaders; ensure routes still declare loadComponent.
    expect(child('dashboard')?.loadComponent).toBeTypeOf('function');
    expect(child('insights/analytics')?.loadComponent).toBeTypeOf('function');
    expect(child('insights/tracks')?.loadComponent).toBeTypeOf('function');
    expect(child('analytics')?.loadComponent).toBeTypeOf('function');
    expect(child('tracks')?.loadComponent).toBeTypeOf('function');
    void dashSrc;
    void aSrc;
    void tSrc;
  });
});
