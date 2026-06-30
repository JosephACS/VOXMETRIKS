import { Injectable, signal } from '@angular/core';

export interface ConfirmDialogOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

export interface ConfirmDialogState extends ConfirmDialogOptions {
  confirmLabel: string;
  cancelLabel: string;
}

@Injectable({ providedIn: 'root' })
export class ConfirmDialogService {
  readonly state = signal<ConfirmDialogState | null>(null);

  private resolver: ((value: boolean) => void) | null = null;

  open(options: ConfirmDialogOptions): Promise<boolean> {
    if (this.resolver) {
      this.resolver(false);
    }
    return new Promise<boolean>((resolve) => {
      this.resolver = resolve;
      this.state.set({
        ...options,
        confirmLabel: options.confirmLabel ?? 'OK',
        cancelLabel: options.cancelLabel ?? 'Cancel',
        danger: options.danger ?? false,
      });
    });
  }

  confirm(): void {
    this.resolver?.(true);
    this.close();
  }

  cancel(): void {
    this.resolver?.(false);
    this.close();
  }

  private close(): void {
    this.state.set(null);
    this.resolver = null;
  }
}
