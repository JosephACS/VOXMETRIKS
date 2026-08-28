import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { UiPreferencesService } from './ui-preferences.service';

describe('UiPreferencesService theme authority', () => {
  const storageKey = 'voxmetrik_ui_prefs';
  const themeChoiceKey = 'voxmetrik_theme_choice';

  beforeEach(() => {
    localStorage.removeItem(storageKey);
    localStorage.removeItem(themeChoiceKey);
    TestBed.configureTestingModule({ providers: [UiPreferencesService] });
  });

  afterEach(() => {
    vi.useRealTimers();
    localStorage.removeItem(storageKey);
    localStorage.removeItem(themeChoiceKey);
  });

  it('hydrates the account theme while the browser still follows system', () => {
    const service = TestBed.inject(UiPreferencesService);
    expect(service.theme()).toBe('system');

    service.syncThemeFromDarkMode(false);

    expect(service.theme()).toBe('light');
  });

  it('does not replace an explicit topbar choice with an async profile response', () => {
    const service = TestBed.inject(UiPreferencesService);
    service.setTheme('dark');

    service.syncThemeFromDarkMode(false);

    expect(service.theme()).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('keeps system as an explicit browser choice when the profile arrives later', () => {
    const service = TestBed.inject(UiPreferencesService);
    service.setTheme('system');

    service.syncThemeFromDarkMode(false);

    expect(service.theme()).toBe('system');
  });

  it('changes theme through the live two-phase fade without browser snapshots', () => {
    vi.useFakeTimers();
    const service = TestBed.inject(UiPreferencesService);
    service.setTheme('dark');

    service.toggleDarkLight();
    expect(document.documentElement.classList.contains('theme-changing')).toBe(true);
    expect(service.theme()).toBe('dark');

    vi.advanceTimersByTime(75);
    expect(service.theme()).toBe('light');
    expect(document.documentElement.classList.contains('theme-changed')).toBe(true);

    vi.advanceTimersByTime(150);
    expect(document.documentElement.classList.contains('theme-changing')).toBe(false);
    expect(document.documentElement.classList.contains('theme-changed')).toBe(false);
  });
});
