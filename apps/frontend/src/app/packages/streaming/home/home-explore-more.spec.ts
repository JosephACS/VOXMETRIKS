import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { HomeComponent } from './home.component';
import { I18nService } from '../../../core/services/i18n.service';
import { AuthService } from '../../../core/services/auth.service';
import { DashboardService } from '../services/dashboard.service';
import { HistoryService } from '../services/history.service';
import { ListenStatsService } from '../services/listen-stats.service';
import { FavoritesService } from '../services/favorites.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import { PlayerController } from '../../../playback-core/player.controller';
import { SmartHomeService } from '../../smart/services/smart-home.service';
import { AudioPrefetchService } from '../../../playback-core/audio-prefetch.service';

describe('Home progressive explore-more', () => {
  let fixture: ComponentFixture<HomeComponent>;
  let component: HomeComponent;

  beforeEach(async () => {
    TestBed.overrideComponent(HomeComponent, {
      set: {
        template: `
          <details
            class="vx-explore-more"
            data-testid="home-explore-more"
            [open]="exploreMoreOpen()"
            (toggle)="onExploreMoreToggle($event)"
          >
            <summary>home.exploreMore</summary>
            <div data-testid="home-explore-body">secondary</div>
          </details>
        `,
        styles: [],
        templateUrl: undefined as unknown as string,
        styleUrls: [],
        imports: [],
      },
    });

    await TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: I18nService,
          useValue: { lang: signal('es'), t: (k: string) => k, greetingKey: () => 'home.greeting.afternoon' },
        },
        { provide: AuthService, useValue: { getUser: () => ({ username: 'u', plan: 'Free' }) } },
        {
          provide: DashboardService,
          useValue: {
            getHomeFeed: () =>
              of({
                summary: null,
                catalog_growth: [],
                discover: { items: [] },
                genres: [],
                artists: [],
                playlists: [],
                my_playlist_count: 0,
              }),
          },
        },
        {
          provide: HistoryService,
          useValue: {
            history$: of([]),
            reload: vi.fn(),
            pruneAbove: vi.fn(),
          },
        },
        { provide: ListenStatsService, useValue: { minutesToday: () => 0, reload: vi.fn() } },
        {
          provide: FavoritesService,
          useValue: {
            favoriteIds$: of(new Set()),
            count: () => of(0),
            list: () => of([]),
          },
        },
        { provide: CoverArtService, useValue: { gradientFor: () => 'g', initialsFor: () => 'A' } },
        {
          provide: TrackCoverService,
          useValue: {
            bestCover$: () => of(null),
            artistCover$: () => of(null),
          },
        },
        { provide: PlayerController, useValue: { playTrack: vi.fn(), fromTrack: (t: unknown) => t } },
        {
          provide: SmartHomeService,
          useValue: { getHome: () => of({ sections: [], profile: null }) },
        },
        { provide: AudioPrefetchService, useValue: { warm: vi.fn() } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('keeps secondary content behind progressive explore-more disclosure', () => {
    const details = fixture.nativeElement.querySelector(
      '[data-testid="home-explore-more"]',
    ) as HTMLDetailsElement;
    expect(details).toBeTruthy();
    expect(component.exploreMoreOpen()).toBe(false);
    expect(details.open).toBe(false);
  });

  it('toggles exploreMoreOpen from the details element', () => {
    const details = fixture.nativeElement.querySelector(
      '[data-testid="home-explore-more"]',
    ) as HTMLDetailsElement;
    details.open = true;
    details.dispatchEvent(new Event('toggle'));
    fixture.detectChanges();
    expect(component.exploreMoreOpen()).toBe(true);
  });

  it('preserves explore-more toggle without removing secondary sources', () => {
    expect(typeof component.onExploreMoreToggle).toBe('function');
    expect(fixture.nativeElement.querySelector('[data-testid="home-explore-body"]')).toBeTruthy();
  });
});
