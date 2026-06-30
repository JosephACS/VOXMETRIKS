import { Directive, ElementRef, Input, OnDestroy, OnInit, inject, signal } from '@angular/core';

/**
 * Defers work until the host element intersects the viewport (root margin preloads slightly).
 */
@Directive({
  selector: '[appDeferVisible]',
  standalone: true,
  exportAs: 'deferVisible',
})
export class DeferVisibleDirective implements OnInit, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);
  private observer: IntersectionObserver | null = null;

  readonly visible = signal(false);

  @Input() rootMargin = '120px';

  ngOnInit(): void {
    if (typeof IntersectionObserver === 'undefined') {
      this.visible.set(true);
      return;
    }
    this.observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          this.visible.set(true);
          this.observer?.disconnect();
          this.observer = null;
        }
      },
      { root: null, rootMargin: this.rootMargin, threshold: 0.01 },
    );
    this.observer.observe(this.el.nativeElement);
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
