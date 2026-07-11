import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-horizontal-section',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  template: `
    <section class="h-section">
      <div class="h-head">
        <h2>{{ title }}</h2>
        @if (subtitle) { <span class="h-sub">{{ subtitle }}</span> }
        @if (link) {
          <a class="h-link" [routerLink]="link">{{ 'home.viewAll' | t:lang() }}</a>
        }
      </div>
      <div class="h-scroll-wrap">
        <div class="h-scroll">
          <ng-content />
        </div>
      </div>
    </section>
  `,
  styles: [`
    .h-section { margin-bottom: 1.25rem; }
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
    }
    .h-link:hover { color: #1ed896; }
    .h-scroll-wrap {
      position: relative;
      margin: 0 -0.25rem;
    }
    .h-scroll-wrap::before,
    .h-scroll-wrap::after {
      content: '';
      position: absolute;
      top: 0;
      bottom: 8px;
      width: 32px;
      z-index: 2;
      pointer-events: none;
    }
    .h-scroll-wrap::before {
      left: 0;
      background: linear-gradient(90deg, var(--bg-base, #0a0a0a) 0%, transparent 100%);
    }
    .h-scroll-wrap::after {
      right: 0;
      background: linear-gradient(270deg, var(--bg-base, #0a0a0a) 0%, transparent 100%);
    }
    .h-scroll {
      display: flex;
      gap: 0.3rem;
      overflow-x: auto;
      overflow-y: hidden;
      overscroll-behavior-x: contain;
      padding: 0.25rem 0.25rem 0.75rem;
      scroll-snap-type: x mandatory;
      scroll-padding-left: 0.25rem;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
    }
    .h-scroll::-webkit-scrollbar { display: none; }
  `],
})
export class HorizontalSectionComponent {
  readonly lang = inject(I18nService).lang;
  @Input({ required: true }) title!: string;
  @Input() subtitle?: string;
  @Input() link?: string;
}
