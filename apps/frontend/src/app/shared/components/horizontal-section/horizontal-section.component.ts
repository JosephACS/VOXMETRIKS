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
          (scroll)="onScroll()"
          (pointerdown)="onPointerDown($event)"
          (wheel)="onWheel($event)"
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
      margin-bottom: 1.25rem;
      position: relative;
    }
    .h-head {
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
      margin-bottom: 0.6rem;
      padding: 0 0.7rem;
    }
    .h-head h2 {
      font-size: 1.25rem;
      font-weight: 700;
      margin: 0;
      letter-spacing: -0.02em;
    }
    .h-sub {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .h-link {
      margin-left: auto;
      font-size: 0.6875rem;
      font-weight: 600;
      color: var(--shell-fg-muted, var(--text-muted));
      text-decoration: none;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      white-space: nowrap;
      z-index: 3;
    }
    .h-link:hover { color: #1ed896; }

    .h-scroll-wrap {
      position: relative;
      margin: 0 -0.25rem;
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
      gap: 0.3rem;
      overflow-x: auto;
      overflow-y: hidden;
      overscroll-behavior-x: contain;
      padding: 0.25rem 0.25rem 0.75rem;
      scroll-snap-type: x proximity;
      scroll-padding-inline: 0.5rem;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      cursor: grab;
      touch-action: pan-x;
    }
    .h-scroll::-webkit-scrollbar { display: none; }
    .h-scroll.is-dragging {
      cursor: grabbing;
      scroll-behavior: auto;
      scroll-snap-type: none;
      user-select: none;
    }
    .h-scroll.is-dragging ::ng-deep * {
      pointer-events: none;
    }

    .h-arrow {
      position: absolute;
      top: 50%;
      transform: translateY(calc(-50% - 8px));
      z-index: 4;
      width: 40px;
      height: 40px;
      border: none;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #fff;
      background: rgba(18, 18, 18, 0.82);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
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
      background: rgba(30, 216, 150, 0.95);
      color: #06150f;
      transform: translateY(calc(-50% - 8px)) scale(1.06);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
    }
    .h-arrow:focus-visible {
      outline: 2px solid #1ed896;
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

  private resizeObs: ResizeObserver | null = null;
  private mutationObs: MutationObserver | null = null;
  private dragStartX = 0;
  private dragScrollLeft = 0;
  private dragMoved = false;
  private dragArmed = false;
  private pointerId: number | null = null;

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
  }

  @HostListener('document:pointermove', ['$event'])
  onDocPointerMove(e: PointerEvent): void {
    if ((!this.dragArmed && !this.dragging()) || this.pointerId !== e.pointerId) return;
    const el = this.scrollerRef.nativeElement;
    const dx = e.clientX - this.dragStartX;
    if (!this.dragMoved && Math.abs(dx) > 6) {
      this.dragMoved = true;
      this.dragging.set(true);
      try {
        el.setPointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
    }
    if (!this.dragMoved) return;
    el.scrollLeft = this.dragScrollLeft - dx;
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

  onWheel(e: WheelEvent): void {
    const el = this.scrollerRef.nativeElement;
    if (!this.hasOverflow()) return;

    // Native trackpads already pan-x; shift+wheel or dominant horizontal delta help mouse users.
    const absX = Math.abs(e.deltaX);
    const absY = Math.abs(e.deltaY);
    if (e.shiftKey && absY > 0) {
      e.preventDefault();
      el.scrollBy({ left: e.deltaY, behavior: 'auto' });
      return;
    }
    if (absX > absY && absX > 0) {
      // Let the browser handle native horizontal wheel; just refresh arrows.
      this.updateScrollState();
    }
  }

  onPointerDown(e: PointerEvent): void {
    if (e.pointerType === 'touch') return; // native swipe
    if (e.button !== 0) return;
    const target = e.target as HTMLElement | null;
    // Don't start drag from cards / interactive controls — clicks must navigate/play.
    if (target?.closest(
      'button, a, input, [role="button"], app-media-card, .media-card, .pl-card, .artist-chip, .genre-chip, .continue-tile',
    )) return;

    const el = this.scrollerRef.nativeElement;
    this.dragArmed = true;
    this.dragMoved = false;
    this.dragging.set(false);
    this.dragStartX = e.clientX;
    this.dragScrollLeft = el.scrollLeft;
    this.pointerId = e.pointerId;
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
    this.updateScrollState();

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
}
