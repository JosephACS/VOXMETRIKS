import { TestBed } from '@angular/core/testing';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot } from '@angular/router';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { AppTitleStrategy } from './app-title.strategy';
import { I18nService } from '../services/i18n.service';

describe('AppTitleStrategy brand', () => {
  it('uses VOXMETRIKS in default and route titles', () => {
    const setTitle = vi.fn();
    TestBed.configureTestingModule({
      providers: [
        AppTitleStrategy,
        { provide: Title, useValue: { setTitle } },
        {
          provide: I18nService,
          useValue: {
            lang: signal('es'),
            t: (key: string) => (key === 'common.missingTranslation' ? 'MISSING' : key),
          },
        },
      ],
    });
    const strategy = TestBed.inject(AppTitleStrategy);
    const snapshot = {} as RouterStateSnapshot;

    vi.spyOn(strategy, 'buildTitle').mockReturnValue('');
    strategy.updateTitle(snapshot);
    expect(setTitle).toHaveBeenCalledWith('VOXMETRIKS — Music Intelligence Platform');

    vi.spyOn(strategy, 'buildTitle').mockReturnValue('Discover');
    strategy.updateTitle(snapshot);
    expect(setTitle).toHaveBeenCalledWith('Discover | VOXMETRIKS');
  });
});
