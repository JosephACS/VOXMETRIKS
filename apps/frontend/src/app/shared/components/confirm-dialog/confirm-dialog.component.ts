import {
  Component,
  ElementRef,
  inject,
  viewChild,
  effect,
  DestroyRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FocusTrap, FocusTrapFactory } from '@angular/cdk/a11y';
import { ConfirmDialogService } from '../../services/confirm-dialog.service';
import { I18nService } from '../../../core/services/i18n.service';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './confirm-dialog.component.html',
  styleUrls: [
    '../../styles/catalog-crud-modal.css',
    './confirm-dialog.component.css',
  ],
})
export class ConfirmDialogComponent {
  private readonly dialog = inject(ConfirmDialogService);
  private readonly i18n = inject(I18nService);
  private readonly focusTrapFactory = inject(FocusTrapFactory);
  private readonly destroyRef = inject(DestroyRef);

  readonly state = this.dialog.state;
  readonly dialogEl = viewChild<ElementRef<HTMLElement>>('dialogPanel');

  readonly titleId = 'app-confirm-dialog-title';
  readonly messageId = 'app-confirm-dialog-message';

  private trap: FocusTrap | null = null;
  private returnFocus: HTMLElement | null = null;

  constructor() {
    effect(() => {
      const open = !!this.state();
      if (open) {
        this.returnFocus = document.activeElement as HTMLElement | null;
        queueMicrotask(() => this.attachTrap());
      } else {
        this.detachTrap();
      }
    });
    this.destroyRef.onDestroy(() => this.detachTrap());
  }

  closeLabel(): string {
    return this.i18n.t('common.close');
  }

  onBackdropClick(): void {
    this.dialog.cancel();
  }

  onCancel(): void {
    this.dialog.cancel();
  }

  onConfirm(): void {
    this.dialog.confirm();
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.dialog.cancel();
    }
  }

  private attachTrap(): void {
    const el = this.dialogEl()?.nativeElement;
    if (!el) return;
    this.detachTrap();
    this.trap = this.focusTrapFactory.create(el);
    this.trap.focusInitialElementWhenReady();
  }

  private detachTrap(): void {
    this.trap?.destroy();
    this.trap = null;
    this.returnFocus?.focus?.();
    this.returnFocus = null;
  }
}
