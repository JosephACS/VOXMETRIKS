import { Injectable } from '@angular/core';

interface CacheEntry<T> {
  value: T;
  expiresAt: number;
}

/** Small session cache for catalog/report GETs. It survives route changes but
 * never becomes a second source of truth for mutations or audio playback. */
@Injectable({ providedIn: 'root' })
export class CatalogCacheService {
  private readonly memory = new Map<string, CacheEntry<unknown>>();
  private readonly prefix = 'voxmetriks:catalog-cache:v1:';

  get<T>(key: string, maxAgeMs = 60_000): T | null {
    const now = Date.now();
    const inMemory = this.memory.get(key) as CacheEntry<T> | undefined;
    if (inMemory && inMemory.expiresAt > now) return inMemory.value;
    this.memory.delete(key);

    try {
      const raw = sessionStorage.getItem(this.prefix + key);
      if (!raw) return null;
      const entry = JSON.parse(raw) as CacheEntry<T>;
      if (!entry || entry.expiresAt <= now) {
        sessionStorage.removeItem(this.prefix + key);
        return null;
      }
      // Do not extend the server freshness window when callers ask for a
      // shorter TTL (useful for report data).
      if (entry.expiresAt - now > maxAgeMs) entry.expiresAt = now + maxAgeMs;
      this.memory.set(key, entry as CacheEntry<unknown>);
      return entry.value;
    } catch {
      return null;
    }
  }

  set<T>(key: string, value: T, ttlMs = 60_000): void {
    const entry: CacheEntry<T> = { value, expiresAt: Date.now() + ttlMs };
    this.memory.set(key, entry as CacheEntry<unknown>);
    try {
      sessionStorage.setItem(this.prefix + key, JSON.stringify(entry));
    } catch {
      // Storage can be disabled/full; memory caching still helps this session.
    }
  }

  invalidate(keyPrefix = ''): void {
    for (const key of this.memory.keys()) {
      if (key.startsWith(keyPrefix)) this.memory.delete(key);
    }
    try {
      for (let i = sessionStorage.length - 1; i >= 0; i -= 1) {
        const key = sessionStorage.key(i);
        if (key?.startsWith(this.prefix + keyPrefix)) sessionStorage.removeItem(key);
      }
    } catch {
      /* ignore storage access errors */
    }
  }
}
