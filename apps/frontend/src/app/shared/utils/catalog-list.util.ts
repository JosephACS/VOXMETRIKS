import { DestroyRef } from '@angular/core';

export function pageWindow(current: number, total: number, delta = 2): number[] {
  const range: number[] = [];
  for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
    range.push(i);
  }
  return range;
}

export function paginatedRowIndex(page: number, limit: number, index: number): number {
  return (page - 1) * limit + index + 1;
}

export function apiFormError(err: unknown, fallback: string): string {
  const detail = (err as { error?: { detail?: string } })?.error?.detail;
  return detail ?? fallback;
}

export function createSearchDebouncer(destroyRef: DestroyRef, delayMs = 350) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  destroyRef.onDestroy(() => {
    if (timer) clearTimeout(timer);
  });
  return {
    schedule(fn: () => void) {
      if (timer) clearTimeout(timer);
      timer = setTimeout(fn, delayMs);
    },
  };
}
