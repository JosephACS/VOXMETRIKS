import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/**
 * Full-viewport shell for “Who’s listening?” — no sidebar, topbar, or player.
 */
@Component({
  selector: 'app-profiles-layout',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="profiles-layout" data-testid="profiles-layout">
      <div class="profiles-layout__bg" aria-hidden="true"></div>
      <div class="profiles-layout__glow" aria-hidden="true"></div>
      <main class="profiles-layout__main">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        min-height: 100vh;
        min-height: 100dvh;
      }
      .profiles-layout {
        position: relative;
        min-height: 100vh;
        min-height: 100dvh;
        overflow: auto;
        background: #07090c;
        color: #f4f7f5;
      }
      .profiles-layout__bg {
        position: fixed;
        inset: 0;
        background:
          radial-gradient(ellipse 80% 55% at 50% -10%, rgba(30, 216, 150, 0.16), transparent 55%),
          radial-gradient(ellipse 50% 40% at 90% 80%, rgba(30, 216, 150, 0.06), transparent 50%),
          linear-gradient(180deg, #0a0e12 0%, #07090c 45%, #050708 100%);
        pointer-events: none;
        z-index: 0;
      }
      .profiles-layout__glow {
        position: fixed;
        inset: 0;
        background-image:
          linear-gradient(90deg, rgba(30, 216, 150, 0.025) 1px, transparent 1px),
          linear-gradient(0deg, rgba(30, 216, 150, 0.025) 1px, transparent 1px);
        background-size: 56px 56px;
        mask-image: radial-gradient(ellipse at center, black 20%, transparent 75%);
        pointer-events: none;
        z-index: 0;
      }
      .profiles-layout__main {
        position: relative;
        z-index: 1;
        min-height: 100vh;
        min-height: 100dvh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: clamp(1.25rem, 4vw, 2.5rem);
      }
      @media (prefers-reduced-motion: reduce) {
        .profiles-layout__bg,
        .profiles-layout__glow {
          transition: none;
        }
      }
    `,
  ],
})
export class ProfilesLayoutComponent {}
