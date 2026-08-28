import { Component, HostBinding, Input } from '@angular/core';

export type BrandMarkVariant = 'horizontal' | 'mark' | 'wordmark';

/** Vector brand system shared by authentication, shell and product surfaces. */
@Component({
  selector: 'app-brand-mark',
  standalone: true,
  template: `
    @if (variant === 'mark') {
      <img
        class="brand-mark brand-mark--icon"
        src="/assets/brand/voxmetriks-mark.svg?v=mono4"
        [alt]="decorative ? '' : ariaLabel"
        [attr.aria-hidden]="decorative ? 'true' : null"
      />
    } @else if (variant === 'wordmark') {
      <span class="brand-mark brand-mark--word" [attr.aria-label]="ariaLabel">VOXMETRIKS</span>
    } @else {
      <img
        class="brand-mark brand-mark--horizontal brand-mark--on-dark"
        src="/assets/brand/voxmetriks-logo-dark.svg?v=mono4"
        [alt]="decorative ? '' : ariaLabel"
        [attr.aria-hidden]="decorative ? 'true' : null"
      />
      <img
        class="brand-mark brand-mark--horizontal brand-mark--on-light"
        src="/assets/brand/voxmetriks-logo-light.svg?v=mono5"
        [alt]="decorative ? '' : ariaLabel"
        [attr.aria-hidden]="decorative ? 'true' : null"
      />
    }
  `,
  styles: [
    `
      :host {
        display: inline-flex;
        line-height: 0;
      }

      .brand-mark--horizontal {
        display: block;
        width: 15rem;
        height: auto;
      }

      .brand-mark--on-light {
        display: none;
      }

      :host-context(html[data-theme='light']) .brand-mark--on-dark {
        display: none;
      }

      :host-context(html[data-theme='light']) .brand-mark--on-light {
        display: block;
      }

      :host(.brand-mark-host--force-dark) .brand-mark--on-dark {
        display: block !important;
      }

      :host(.brand-mark-host--force-dark) .brand-mark--on-light {
        display: none !important;
      }

      .brand-mark--icon {
        width: 2.25rem;
        height: 2.25rem;
      }

      :host-context(html[data-theme='light']) .brand-mark--icon {
        filter: invert(1);
      }

      .brand-mark--word {
        font-family: var(--font-sans, 'Inter', sans-serif);
        font-size: 1.125rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #fff;
        line-height: 1;
      }

      :host(.brand-mark-host--lg) .brand-mark--horizontal {
        width: 18rem;
      }

      :host(.brand-mark-host--sm) .brand-mark--horizontal {
        width: 11rem;
      }

      :host(.brand-mark-host--sm) .brand-mark--word {
        font-size: 0.9375rem;
      }

      :host(.brand-mark-host--sm) .brand-mark--icon {
        width: 1.75rem;
        height: 1.75rem;
      }
    `,
  ],
})
export class BrandMarkComponent {
  @Input() variant: BrandMarkVariant = 'horizontal';
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
  @Input() decorative = false;
  @Input() ariaLabel = 'VOXMETRIKS';
  @Input() tone: 'auto' | 'dark' = 'auto';

  @HostBinding('class.brand-mark-host--sm') get isSm(): boolean {
    return this.size === 'sm';
  }
  @HostBinding('class.brand-mark-host--lg') get isLg(): boolean {
    return this.size === 'lg';
  }
  @HostBinding('class.brand-mark-host--force-dark') get isForcedDark(): boolean {
    return this.tone === 'dark';
  }
}
