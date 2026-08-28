import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { HorizontalSectionComponent } from './horizontal-section.component';

describe('HorizontalSectionComponent gestures', () => {
  function setup() {
    TestBed.configureTestingModule({
      imports: [HorizontalSectionComponent],
      providers: [provideRouter([])],
    });
    const fixture = TestBed.createComponent(HorizontalSectionComponent);
    fixture.componentRef.setInput('title', 'Prueba');
    fixture.detectChanges();
    const component = fixture.componentInstance;
    const scroller = component.scrollerRef.nativeElement;
    Object.defineProperty(scroller, 'scrollWidth', { configurable: true, value: 900 });
    Object.defineProperty(scroller, 'clientWidth', { configurable: true, value: 320 });
    return { fixture, component, scroller };
  }

  it('allows mouse dragging to begin from a card surface', () => {
    const { fixture, component, scroller } = setup();
    const card = document.createElement('article');
    card.className = 'media-card';
    scroller.appendChild(card);

    component.onPointerDown({
      pointerType: 'mouse', button: 0, target: card, clientX: 120, clientY: 40, pointerId: 7,
    } as unknown as PointerEvent);
    component.onDocPointerMove({
      clientX: 90, clientY: 41, pointerId: 7, preventDefault: vi.fn(),
    } as unknown as PointerEvent);

    expect(component.dragging()).toBe(true);
    expect(scroller.scrollLeft).toBeGreaterThan(0);
    fixture.destroy();
  });

  it('yields to a vertical gesture instead of hijacking page scroll', () => {
    const { fixture, component, scroller } = setup();

    component.onPointerDown({
      pointerType: 'mouse', button: 0, target: scroller, clientX: 120, clientY: 40, pointerId: 8,
    } as unknown as PointerEvent);
    component.onDocPointerMove({
      clientX: 118, clientY: 70, pointerId: 8, preventDefault: vi.fn(),
    } as unknown as PointerEvent);
    component.onDocPointerMove({
      clientX: 80, clientY: 71, pointerId: 8, preventDefault: vi.fn(),
    } as unknown as PointerEvent);

    expect(component.dragging()).toBe(false);
    expect(scroller.scrollLeft).toBe(0);
    fixture.destroy();
  });
});
