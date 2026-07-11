import { Injectable, inject, DestroyRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { NotificationService } from './notification.service';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class PlatformEventsService {
  private readonly http = inject(HttpClient);
  private readonly notifications = inject(NotificationService);
  private readonly auth = inject(AuthService);
  private readonly base = `${environment.apiUrl}/platform`;
  private source: EventSource | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private lastSeenId: string | null = null;

  start(destroyRef: DestroyRef): void {
    if (!this.auth.isAuthenticated()) return;
    this.startPolling(destroyRef);
  }

  private startPolling(destroyRef: DestroyRef): void {
    this.pollTimer = setInterval(() => this.pollNotifications(), 30_000);
    this.pollNotifications();
    destroyRef.onDestroy(() => this.stop());
  }

  private pollNotifications(): void {
    if (!this.auth.isAuthenticated()) return;
    this.http.get<{ notifications: Array<{ id: string; title: string; message: string; level?: string }> }>(
      `${this.base}/notifications`,
    ).subscribe({
      next: (res) => {
        const items = res.notifications ?? [];
        if (!items.length) return;
        const newest = items[0];
        if (this.lastSeenId && newest.id === this.lastSeenId) return;
        this.lastSeenId = newest.id;
        if (items.length === 1 || !this.lastSeenId) {
          this.notifications.fromServer(newest);
        }
      },
      error: () => { /* silent fallback */ },
    });
  }

  stop(): void {
    this.stopSse();
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private stopSse(): void {
    this.source?.close();
    this.source = null;
  }
}
