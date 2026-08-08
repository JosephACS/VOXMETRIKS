/**
 * Global Vitest setup for Angular unit tests (jsdom).
 * Polyfills browser APIs that the app relies on but jsdom does not ship.
 */

import { getTestBed } from '@angular/core/testing';
import {
  BrowserTestingModule,
  platformBrowserTesting,
} from '@angular/platform-browser/testing';

// Angular's unit-test builder may already init TestBed; plain `vitest run` does not.
const testBed = getTestBed();
if (!(testBed as { platform?: unknown }).platform) {
  testBed.initTestEnvironment(BrowserTestingModule, platformBrowserTesting());
}

/** In-memory Storage implementation for localStorage / sessionStorage. */
function memoryStorage(): Storage {
  let store: Record<string, string> = {};
  return {
    get length() {
      return Object.keys(store).length;
    },
    clear() {
      store = {};
    },
    getItem(key: string) {
      return store[key] ?? null;
    },
    key(index: number) {
      return Object.keys(store)[index] ?? null;
    },
    removeItem(key: string) {
      delete store[key];
    },
    setItem(key: string, value: string) {
      store[key] = String(value);
    },
  };
}

if (typeof globalThis.localStorage === 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', { value: memoryStorage() });
}
if (typeof globalThis.sessionStorage === 'undefined') {
  Object.defineProperty(globalThis, 'sessionStorage', { value: memoryStorage() });
}

if (typeof window !== 'undefined' && typeof window.matchMedia !== 'function') {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string): MediaQueryList => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }),
  });
}

/** jsdom ships HTMLAudioElement but play()/pause() are stubs that return undefined. */
if (typeof HTMLMediaElement !== 'undefined') {
  HTMLMediaElement.prototype.play = function play() {
    return Promise.resolve();
  };
  HTMLMediaElement.prototype.pause = function pause() {
    return undefined;
  };
  HTMLMediaElement.prototype.load = function load() {
    return undefined;
  };
}
