import { Component, HostBinding, Input } from '@angular/core';

export type BrandMarkVariant = 'horizontal' | 'mark' | 'wordmark';

/**
 * Temporary solid brand system for dark UI surfaces.
 * Variants: horizontal (isotype + wordmark), mark (isotype only), wordmark.
 */
@Component({
  selector: 'app-brand-mark',
  standalone: true,
  template: `
    @if (variant === 'mark') {
      <svg
        class="brand-mark brand-mark--icon"
        viewBox="0 0 48 48"
        role="img"
        [attr.aria-label]="ariaLabel"
        [attr.aria-hidden]="decorative ? 'true' : null"
      >
        <rect width="48" height="48" rx="12" fill="rgba(30,216,150,0.1)" />
        <path
          d="M12 34 L24 12 L36 34"
          fill="none"
          stroke="#1ed896"
          stroke-width="3.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <path
          d="M17.5 34 L24 22 L30.5 34"
          fill="none"
          stroke="rgba(255,255,255,0.85)"
          stroke-width="2.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <g fill="#1ed896">
          <rect x="19" y="28" width="2.2" height="5" rx="1.1" />
          <rect x="23" y="25.5" width="2.2" height="7.5" rx="1.1" />
          <rect x="27" y="27" width="2.2" height="6" rx="1.1" />
        </g>
      </svg>
    } @else if (variant === 'wordmark') {
      <span class="brand-mark brand-mark--word" [attr.aria-label]="ariaLabel">VOXMETRIKS</span>
    } @else {
      <div
        class="brand-mark brand-mark--horizontal"
        role="img"
        [attr.aria-label]="ariaLabel"
        [attr.aria-hidden]="decorative ? 'true' : null"
      >
        <svg class="brand-mark__iso" viewBox="0 0 48 48" aria-hidden="true">
          <rect width="48" height="48" rx="12" fill="rgba(30,216,150,0.1)" />
          <path
            d="M12 34 L24 12 L36 34"
            fill="none"
            stroke="#1ed896"
            stroke-width="3.2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M17.5 34 L24 22 L30.5 34"
            fill="none"
            stroke="rgba(255,255,255,0.85)"
            stroke-width="2.2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <g fill="#1ed896">
            <rect x="19" y="28" width="2.2" height="5" rx="1.1" />
            <rect x="23" y="25.5" width="2.2" height="7.5" rx="1.1" />
            <rect x="27" y="27" width="2.2" height="6" rx="1.1" />
          </g>
        </svg>
        <span class="brand-mark__name">VOXMETRIKS</span>
      </div>
    }
  `,
  styles: [
    `
      :host {
        display: inline-flex;
        line-height: 0;
      }

      .brand-mark--horizontal {
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
      }

      .brand-mark__iso {
        width: 2.75rem;
        height: 2.75rem;
        flex-shrink: 0;
      }

      .brand-mark--icon {
        width: 2.25rem;
        height: 2.25rem;
      }

      .brand-mark__name,
      .brand-mark--word {
        font-family: var(--font-sans, 'Inter', sans-serif);
        font-size: 1.125rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #fff;
        line-height: 1;
      }

      :host(.brand-mark-host--lg) .brand-mark__iso {
        width: 3.5rem;
        height: 3.5rem;
      }

      :host(.brand-mark-host--lg) .brand-mark__name {
        font-size: 1.5rem;
        letter-spacing: 0.1em;
      }

      :host(.brand-mark-host--sm) .brand-mark__iso {
        width: 2rem;
        height: 2rem;
      }

      :host(.brand-mark-host--sm) .brand-mark__name,
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

  @HostBinding('class.brand-mark-host--sm') get isSm(): boolean {
    return this.size === 'sm';
  }
  @HostBinding('class.brand-mark-host--lg') get isLg(): boolean {
    return this.size === 'lg';
  }
}
