import { Injectable, signal } from '@angular/core';

export type NotificationLevel = 'info' | 'success' | 'warning' | 'error';

export interface AppNotification {
  id: string;
  level: NotificationLevel;
  title: string;
  message: string;
  createdAt: number;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly _items = signal<AppNotification[]>([]);
  readonly items = this._items.asReadonly();

  show(title: string, message: string, level: NotificationLevel = 'info', ttlMs = 4500): void {
    const id = crypto.randomUUID?.() ?? String(Date.now() + Math.random());
    const note: AppNotification = {
      id,
      level,
      title,
      message,
      createdAt: Date.now(),
    };
    this._items.update((list) => [note, ...list].slice(0, 8));
    if (ttlMs > 0) {
      setTimeout(() => this.dismiss(id), ttlMs);
    }
  }

  success(title: string, message = ''): void {
    this.show(title, message, 'success');
  }

  info(title: string, message = ''): void {
    this.show(title, message, 'info');
  }

  warning(title: string, message = ''): void {
    this.show(title, message, 'warning');
  }

  error(title: string, message = ''): void {
    this.show(title, message, 'error', 6000);
  }

  dismiss(id: string): void {
    this._items.update((list) => list.filter((n) => n.id !== id));
  }

  fromServer(payload: { title: string; message: string; level?: string }): void {
    const level = (payload.level as NotificationLevel) ?? 'info';
    this.show(payload.title, payload.message, level);
  }
}
