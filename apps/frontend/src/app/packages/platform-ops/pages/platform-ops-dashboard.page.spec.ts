import { describe, expect, it, vi, beforeEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { PlatformOpsDashboardPage } from './platform-ops-dashboard.page';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import { PLATFORM_OPS_ROUTES } from '../platform-ops.routes';
import {
  listVisibleContextTabs,
  listVisibleSidebarSurfaces,
  resolveSurfacePath,
  STAFF_CAPABILITY,
  type ProductSurfaceContext,
} from '../../../core/product-surface';
import { resolveModuleContext } from '../../../shared/navigation/module-context';

describe('Spec 055 platform ops dashboard + registry', () => {
  it('registers /platform-ops/system in registry and context tabs', () => {
    const ctx: ProductSurfaceContext = {
      ready: true,
      activeSpace: 'platform_admin',
      permissions: new Set(),
      artistCapabilities: new Set(),
      staffCapabilities: new Set([STAFF_CAPABILITY.shell]),
      platformRoles: new Set(),
    };
    const paths = listVisibleSidebarSurfaces(ctx).map((s) => resolveSurfacePath(s));
    expect(paths).toContain('/platform-ops');
    expect(paths).toContain('/platform-ops/system');
    expect(paths).toContain('/platform-ops/artist-requests');
    expect(paths).toContain('/platform-ops/catalog-reviews');

    const tabs = listVisibleContextTabs('platformOps', ctx).map((s) => s.path);
    expect(tabs).toContain('/platform-ops/system');

    const module = resolveModuleContext('/platform-ops/system', ctx);
    expect(module?.moduleId).toBe('platformOps');
    expect(module?.tabs.some((t) => t.path === '/platform-ops/system')).toBe(true);
  });

  it('PLATFORM_OPS_ROUTES includes system path', () => {
    expect(PLATFORM_OPS_ROUTES.some((r) => r.path === 'platform-ops/system')).toBe(true);
    expect(PLATFORM_OPS_ROUTES.some((r) => r.path === 'platform-ops')).toBe(true);
  });

  it('dashboard load only requests overview', async () => {
    const api = {
      getOverview: vi.fn().mockReturnValue(
        of({
          health: 'degraded',
          generated_at: new Date().toISOString(),
          queues: [
            {
              code: 'artist_requests',
              count: 2,
              availability: 'available',
              severity: 'attention',
            },
          ],
          next_queue: 'artist_requests',
          has_pending_work: true,
        }),
      ),
      getHealth: vi.fn(),
      listProviders: vi.fn(),
      listJobs: vi.fn(),
      listFlags: vi.fn(),
      listBackups: vi.fn(),
    };
    await TestBed.configureTestingModule({
      imports: [PlatformOpsDashboardPage],
      providers: [
        provideHttpClient(),
        provideRouter([]),
        { provide: PlatformOpsApiService, useValue: api },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(PlatformOpsDashboardPage);
    const page = fixture.componentInstance;
    page.load();
    expect(api.getOverview).toHaveBeenCalled();
    expect(api.getHealth).not.toHaveBeenCalled();
    expect(api.listProviders).not.toHaveBeenCalled();
    expect(api.listJobs).not.toHaveBeenCalled();
    expect(api.listFlags).not.toHaveBeenCalled();
    expect(api.listBackups).not.toHaveBeenCalled();
    expect(page.overview()?.next_queue).toBe('artist_requests');
  });
});
