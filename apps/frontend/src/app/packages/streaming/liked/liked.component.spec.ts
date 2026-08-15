import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { I18nService } from '../../../core/services/i18n.service';
import { FavoritesStore } from '../../../playback-core/favorites.store';
import { PlayerController } from '../../../playback-core/player.controller';
import { LikedComponent } from './liked.component';

describe('LikedComponent', () => {
  let fixture: ComponentFixture<LikedComponent>;
  const loadFavorites = vi.fn(() => of([]));

  beforeEach(async () => {
    loadFavorites.mockClear();
    await TestBed.configureTestingModule({
      imports: [LikedComponent],
      providers: [
        provideRouter([]),
        {
          provide: I18nService,
          useValue: { lang: signal('es'), t: (key: string) => key },
        },
        {
          provide: FavoritesStore,
          useValue: {
            favoriteIds: signal(new Set<number>()),
            loadFavorites,
          },
        },
        { provide: PlayerController, useValue: { setQueue: vi.fn() } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LikedComponent);
  });

  it('initializes its reactive favorites subscription inside the injection context', () => {
    expect(() => fixture.detectChanges()).not.toThrow();
    expect(loadFavorites).toHaveBeenCalledOnce();
    expect(fixture.componentInstance.hasError()).toBe(false);
  });
});
