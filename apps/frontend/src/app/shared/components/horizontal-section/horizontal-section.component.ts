import {
  AfterViewInit,
  Component,
  DestroyRef,
  ElementRef,
  HostListener,
  Input,
  OnDestroy,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { fromEvent } from 'rxjs';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../pipes/translate.pipe';

/**
 * Spotify-style horizontal content rail with edge fades, arrow navigation,
 * smooth page scrolling, and touch/mouse support.
 */
@Component({
  selector: 'app-horizontal-section',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  template: `
    <section
      class="h-section"
      [class.h-section--hover]="hovered()"
      (mouseenter)="hovered.set(true)"
      (mouseleave)="onLeave()"
    >
      <div class="h-head">
        <h2>{{ title }}</h2>
        @if (subtitle) {
          <span class="h-sub">{{ subtitle }}</span>
        }
        @if (link) {
          <a class="h-link" [routerLink]="link" [queryParams]="queryParams || null">{{ 'home.viewAll' | t:lang() }}</a>
        }
      </div>

      <div class="h-scroll-wrap" [class.has-overflow]="hasOverflow()">
        @if (hasOverflow() && canScrollLeft()) {
          <button
            type="button"
            class="h-arrow h-arrow--left"
            (click)="scrollByPage(-1); $event.stopPropagation()"
            [attr.aria-label]="'home.rail.scrollLeft' | t:lang()"
            [title]="'home.rail.scrollLeft' | t:lang()"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>
        }

        <div
          #scroller
          class="h-scroll"
          [class.is-dragging]="dragging()"
          [class.is-gliding]="gliding()"
          (scroll)="onScroll()"
          (pointerdown)="onPointerDown($event)"
        >
          <ng-content />
        </div>

        @if (hasOverflow() && canScrollRight()) {
          <button
            type="button"
            class="h-arrow h-arrow--right"
            (click)="scrollByPage(1); $event.stopPropagation()"
            [attr.aria-label]="'home.rail.scrollRight' | t:lang()"
            [title]="'home.rail.scrollRight' | t:lang()"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        }
      </div>
    </section>
  `,
  styles: [`
    .h-section {
      margin-bottom: 2rem;
      position: relative;
    }
    .h-head {
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
      margin-bottom: 0.95rem;
      padding: 0 0.15rem;
    }
    .h-head h2 {
      font-size: clamp(1.35rem, 2vw, 1.75rem);
      font-weight: 690;
      margin: 0;
      letter-spacing: -0.045em;
      line-height: 1.05;
    }
    .h-sub {
      max-width: 38rem;
      font-size: 0.76rem;
      color: var(--text-muted);
    }
    .h-link {
      margin-left: auto;
      font-size: 0.625rem;
      font-weight: 680;
      color: var(--shell-fg-muted, var(--text-muted));
      text-decoration: none;
      text-transform: uppercase;
      letter-spacing: 0.11em;
      white-space: nowrap;
      z-index: 3;
    }
    .h-link:hover { color: var(--vx-accent, #e8a33d); }

    .h-scroll-wrap {
      position: relative;
      margin: 0 -0.2rem;
    }
    .h-scroll-wrap.has-overflow::before,
    .h-scroll-wrap.has-overflow::after {
      content: '';
      position: absolute;
      top: 0;
      bottom: 8px;
      width: 40px;
      z-index: 2;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s ease;
    }
    .h-section--hover .h-scroll-wrap.has-overflow::before,
    .h-section--hover .h-scroll-wrap.has-overflow::after {
      opacity: 1;
    }
    .h-scroll-wrap.has-overflow::before {
      left: 0;
      background: linear-gradient(90deg, var(--bg-base, #0a0a0a) 20%, transparent 100%);
    }
    .h-scroll-wrap.has-overflow::after {
      right: 0;
      background: linear-gradient(270deg, var(--bg-base, #0a0a0a) 20%, transparent 100%);
    }

    .h-scroll {
      display: flex;
      gap: 1rem;
      overflow-x: auto;
      overflow-y: hidden;
      overscroll-behavior-x: contain;
      padding: 0.35rem 0.2rem 1.15rem;
      scroll-snap-type: x proximity;
      scroll-padding-inline: 0.5rem;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      cursor: grab;
      touch-action: pan-x pan-y pinch-zoom;
      contain: layout style paint;
    }
    .h-scroll::-webkit-scrollbar { display: none; }
    .h-scroll.is-dragging {
      cursor: grabbing;
      scroll-behavior: auto;
      scroll-snap-type: none;
      user-select: none;
    }
    .h-scroll.is-gliding {
      scroll-behavior: auto;
      scroll-snap-type: none;
    }
    .h-scroll.is-dragging ::ng-deep * {
      pointer-events: none;
    }

    .h-arrow {
      position: absolute;
      top: 50%;
      transform: translateY(calc(-50% - 8px));
      z-index: 4;
      width: 44px;
      height: 44px;
      border: none;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #fff;
      background: rgba(9, 10, 15, 0.82);
      backdrop-filter: blur(18px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.48);
      border: 1px solid rgba(255, 255, 255, 0.12);
      opacity: 0;
      pointer-events: none;
      transition:
        opacity 0.2s ease,
        background 0.15s ease,
        transform 0.15s ease,
        box-shadow 0.15s ease;
    }
    .h-section--hover .h-arrow,
    .h-arrow:focus-visible {
      opacity: 1;
      pointer-events: auto;
    }
    .h-arrow:hover {
      background: rgba(247, 245, 252, 0.96);
      color: #090a0f;
      transform: translateY(calc(-50% - 8px)) scale(1.06);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
    }
    .h-arrow:focus-visible {
      outline: 2px solid var(--vx-accent, #e8a33d);
      outline-offset: 2px;
    }
    .h-arrow:active {
      transform: translateY(calc(-50% - 8px)) scale(0.96);
    }
    .h-arrow--left { left: 4px; }
    .h-arrow--right { right: 4px; }

    @media (hover: none), (max-width: 768px) {
      .h-arrow {
        opacity: 0.72;
        pointer-events: auto;
        width: 34px;
        height: 34px;
      }
      .h-section--hover .h-scroll-wrap.has-overflow::before,
      .h-section--hover .h-scroll-wrap.has-overflow::after,
      .h-scroll-wrap.has-overflow::before,
      .h-scroll-wrap.has-overflow::after {
        opacity: 0.55;
      }
      .h-scroll { cursor: default; }
    }

    @media (prefers-reduced-motion: reduce) {
      .h-scroll { scroll-behavior: auto; }
      .h-arrow { transition: none; }
    }
  `],
})
export class HorizontalSectionComponent implements AfterViewInit, OnDestroy {
  readonly lang = inject(I18nService).lang;
  private readonly destroyRef = inject(DestroyRef);

  @Input({ required: true }) title!: string;
  @Input() subtitle?: string;
  @Input() link?: string;
  @Input() queryParams?: Record<string, string | number | boolean> | null;

  @ViewChild('scroller', { static: true }) scrollerRef!: ElementRef<HTMLElement>;

  hovered = signal(false);
  hasOverflow = signal(false);
  canScrollLeft = signal(false);
  canScrollRight = signal(false);
  dragging = signal(false);
  gliding = signal(false);

  private resizeObs: ResizeObserver | null = null;
  private mutationObs: MutationObserver | null = null;
  private dragStartX = 0;
  private dragStartY = 0;
  private dragScrollLeft = 0;
  private dragMoved = false;
  private dragArmed = false;
  private pointerId: number | null = null;
  private lastPointerX = 0;
  private lastPointerAt = 0;
  private scrollVelocity = 0;
  private glideFrame: number | null = null;

  ngAfterViewInit(): void {
    const el = this.scrollerRef.nativeElement;
    queueMicrotask(() => this.updateScrollState());

    if (typeof ResizeObserver !== 'undefined') {
      this.resizeObs = new ResizeObserver(() => this.updateScrollState());
      this.resizeObs.observe(el);
    }
    if (typeof MutationObserver !== 'undefined') {
      this.mutationObs = new MutationObserver(() => this.updateScrollState());
      this.mutationObs.observe(el, { childList: true, subtree: true });
    }

    fromEvent(window, 'resize')
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.updateScrollState());
  }

  ngOnDestroy(): void {
    this.resizeObs?.disconnect();
    this.mutationObs?.disconnect();
    this.endDrag();
    this.cancelGlide();
  }

  @HostListener('document:pointermove', ['$event'])
  onDocPointerMove(e: PointerEvent): void {
    if ((!this.dragArmed && !this.dragging()) || this.pointerId !== e.pointerId) return;
    const el = this.scrollerRef.nativeElement;
    const dx = e.clientX - this.dragStartX;
    const dy = e.clientY - this.dragStartY;
    if (!this.dragMoved && Math.abs(dy) > 6 && Math.abs(dy) > Math.abs(dx) * 1.15) {
      this.dragArmed = false;
      this.pointerId = null;
      return;
    }
    if (!this.dragMoved && Math.abs(dx) > 6 && Math.abs(dx) > Math.abs(dy) * 1.15) {
      this.dragMoved = true;
      this.dragging.set(true);
      try {
        el.setPointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
    }
    if (!this.dragMoved) return;
    e.preventDefault();
    el.scrollLeft = this.dragScrollLeft - dx;
    const now = performance.now();
    const elapsed = Math.max(1, now - this.lastPointerAt);
    const instantVelocity = (this.lastPointerX - e.clientX) / elapsed;
    this.scrollVelocity = this.scrollVelocity * 0.68 + instantVelocity * 0.32;
    this.lastPointerX = e.clientX;
    this.lastPointerAt = now;
  }

  @HostListener('document:pointerup', ['$event'])
  @HostListener('document:pointercancel', ['$event'])
  onDocPointerUp(e: PointerEvent): void {
    if (this.pointerId !== e.pointerId) return;
    this.endDrag();
  }

  onLeave(): void {
    if (!this.dragging()) this.hovered.set(false);
  }

  onScroll(): void {
    this.updateScrollState();
  }

  onPointerDown(e: PointerEvent): void {
    if (e.pointerType === 'touch') return; // native swipe
    if (e.button !== 0) return;
    const target = e.target as HTMLElement | null;
    // Keep native controls clickable. Card surfaces are draggable; the click is
    // suppressed only when the pointer really moved past the drag threshold.
    if (target?.closest('button, a, input, select, textarea, [contenteditable="true"]')) return;

    const el = this.scrollerRef.nativeElement;
    this.cancelGlide();
    this.dragArmed = true;
    this.dragMoved = false;
    this.dragging.set(false);
    this.dragStartX = e.clientX;
    this.dragStartY = e.clientY;
    this.dragScrollLeft = el.scrollLeft;
    this.pointerId = e.pointerId;
    this.lastPointerX = e.clientX;
    this.lastPointerAt = performance.now();
    this.scrollVelocity = 0;
  }

  scrollByPage(direction: -1 | 1): void {
    const el = this.scrollerRef.nativeElement;
    const amount = this.pageScrollAmount(el);
    el.scrollBy({ left: direction * amount, behavior: 'smooth' });
    // Refresh after smooth scroll settles.
    window.setTimeout(() => this.updateScrollState(), 350);
  }

  private pageScrollAmount(el: HTMLElement): number {
    // ~90% of visible width so the next cards peek in (Spotify-like).
    const base = Math.max(160, el.clientWidth * 0.88);
    const firstCard = el.querySelector(':scope > *') as HTMLElement | null;
    if (firstCard) {
      const style = getComputedStyle(el);
      const gap = parseFloat(style.columnGap || style.gap || '0') || 0;
      const cardW = firstCard.getBoundingClientRect().width + gap;
      if (cardW > 40) {
        const n = Math.max(1, Math.floor(el.clientWidth / cardW));
        return Math.max(cardW, n * cardW - gap);
      }
    }
    return base;
  }

  private updateScrollState(): void {
    const el = this.scrollerRef?.nativeElement;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    const overflow = max > 8;
    this.hasOverflow.set(overflow);
    this.canScrollLeft.set(overflow && el.scrollLeft > 4);
    this.canScrollRight.set(overflow && el.scrollLeft < max - 4);
  }

  private endDrag(): void {
    if (!this.dragArmed && !this.dragging()) return;
    const el = this.scrollerRef.nativeElement;
    const wasDrag = this.dragMoved;
    if (this.pointerId != null) {
      try {
        el.releasePointerCapture(this.pointerId);
      } catch {
        /* ignore */
      }
    }
    this.dragArmed = false;
    this.dragging.set(false);
    this.pointerId = null;
    this.dragMoved = false;
    if (wasDrag && Math.abs(this.scrollVelocity) > 0.08) {
      this.startGlide(this.scrollVelocity);
    } else {
      this.updateScrollState();
    }

    // Suppress the click that follows a drag so play/navigation don't fire.
    if (wasDrag) {
      const suppress = (ev: Event) => {
        ev.preventDefault();
        ev.stopPropagation();
        el.removeEventListener('click', suppress, true);
      };
      el.addEventListener('click', suppress, true);
      window.setTimeout(() => el.removeEventListener('click', suppress, true), 0);
    }
  }

  private startGlide(initialVelocity: number): void {
    this.cancelGlide();
    const el = this.scrollerRef.nativeElement;
    const max = Math.max(0, el.scrollWidth - el.clientWidth);
    let velocity = Math.max(-2.4, Math.min(2.4, initialVelocity));
    let last = performance.now();
    this.gliding.set(true);

    const step = (now: number) => {
      const elapsed = Math.min(32, now - last);
      last = now;
      const before = el.scrollLeft;
      el.scrollLeft = Math.max(0, Math.min(max, before + velocity * elapsed));
      velocity *= Math.pow(0.92, elapsed / 16.67);

      const hitEdge = el.scrollLeft === before && Math.abs(velocity) > 0.02;
      if (Math.abs(velocity) < 0.025 || hitEdge) {
        this.cancelGlide();
        this.updateScrollState();
        return;
      }
      this.glideFrame = requestAnimationFrame(step);
    };

    this.glideFrame = requestAnimationFrame(step);
  }

  private cancelGlide(): void {
    if (this.glideFrame !== null) cancelAnimationFrame(this.glideFrame);
    this.glideFrame = null;
    this.gliding.set(false);
  }
}
