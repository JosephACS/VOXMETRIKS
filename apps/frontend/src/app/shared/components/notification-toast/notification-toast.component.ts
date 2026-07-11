import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-notification-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="toast-stack" aria-live="polite">
      @for (n of notifications.items(); track n.id) {
        <div class="toast toast--{{ n.level }}" role="status">
          <div class="toast-body">
            <strong>{{ n.title }}</strong>
            @if (n.message) {
              <span>{{ n.message }}</span>
            }
          </div>
          <button type="button" class="toast-close" (click)="notifications.dismiss(n.id)" aria-label="Cerrar">×</button>
        </div>
      }
    </div>
  `,
  styles: [`
    .toast-stack {
      position: fixed;
      top: 1rem;
      right: 1rem;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: min(360px, calc(100vw - 2rem));
      pointer-events: none;
    }
    .toast {
      pointer-events: auto;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem 0.85rem;
      border-radius: 10px;
      background: rgba(18, 18, 22, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      animation: slideIn 0.2s ease;
    }
    .toast--success { border-left: 3px solid #1ed896; }
    .toast--info { border-left: 3px solid #3b82f6; }
    .toast--warning { border-left: 3px solid #f59e0b; }
    .toast--error { border-left: 3px solid #ef4444; }
    .toast-body {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      font-size: 0.85rem;
      color: #f3f4f6;
    }
    .toast-body span { color: #9ca3af; font-size: 0.8rem; }
    .toast-close {
      background: none;
      border: none;
      color: #9ca3af;
      font-size: 1.1rem;
      cursor: pointer;
      line-height: 1;
      padding: 0;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateX(12px); }
      to { opacity: 1; transform: translateX(0); }
    }
  `],
})
export class NotificationToastComponent {
  readonly notifications = inject(NotificationService);
}
