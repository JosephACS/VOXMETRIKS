import { Injectable, inject, signal, computed } from '@angular/core';
import { AuthService } from '../../../core/services/auth.service';

const STORAGE_PREFIX = 'voxmetrik_listen_stats';

interface ListenDayRecord {
  date: string;
  seconds: number;
}

function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Real listened seconds today — persisted per user in localStorage. */
@Injectable({ providedIn: 'root' })
export class ListenStatsService {
  private auth = inject(AuthService);
  private record = signal<ListenDayRecord>({ date: todayKey(), seconds: 0 });

  readonly minutesToday = computed(() => {
    const r = this.record();
    if (r.date !== todayKey()) return 0;
    return Math.max(0, Math.round(r.seconds / 60));
  });

  constructor() {
    this.reload();
  }

  reload(): void {
    const today = todayKey();
    try {
      const raw = localStorage.getItem(this.storageKey());
      const parsed: ListenDayRecord = raw ? JSON.parse(raw) : { date: today, seconds: 0 };
      if (parsed.date !== today) {
        this.persist({ date: today, seconds: 0 });
      } else {
        this.record.set(parsed);
      }
    } catch {
      this.persist({ date: today, seconds: 0 });
    }
  }

  /** Accumulate playback time while the player is active (~1s per tick). */
  tick(deltaSec = 1): void {
    if (deltaSec <= 0) return;
    const today = todayKey();
    const cur = this.record();
    const base = cur.date === today ? cur.seconds : 0;
    this.persist({ date: today, seconds: base + deltaSec });
  }

  private persist(r: ListenDayRecord): void {
    this.record.set(r);
    try {
      localStorage.setItem(this.storageKey(), JSON.stringify(r));
    } catch {
      /* quota / private mode */
    }
  }

  private storageKey(): string {
    return `${STORAGE_PREFIX}_${this.auth.userId() ?? 'guest'}`;
  }
}
