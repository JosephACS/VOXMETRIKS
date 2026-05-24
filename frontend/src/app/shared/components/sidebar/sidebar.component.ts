import { Component, Output, EventEmitter, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, RouterLinkActive } from '@angular/router';
import { IconRenderService } from '../../services/icon-render.service';
import { SafeHtml } from '@angular/platform-browser';

interface MenuItem {
  label: string;
  iconSvg: string;
  route: string;
  badge?: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterLinkActive],
  template: `
    <aside class="sidebar" [class.collapsed]="!isOpen">
      <div class="sidebar-header">
        <div class="logo-container">
          <img src="/assets/images/voxmetrik-icon.webp" alt="VOXMETRIK" class="logo-image" />
          <span class="logo-text" *ngIf="isOpen">VOXMETRIK</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <span class="section-title" *ngIf="isOpen">MAIN</span>
          <a
            *ngFor="let item of mainMenu"
            [routerLink]="item.route"
            routerLinkActive="active"
            [routerLinkActiveOptions]="{ exact: true }"
            class="nav-item"
            [title]="item.label"
          >
            <span class="nav-icon" [innerHTML]="safeSvg(item.iconSvg)"></span>
            <span class="nav-label" *ngIf="isOpen">{{ item.label }}</span>
            <span class="nav-badge" *ngIf="item.badge && isOpen">{{ item.badge }}</span>
          </a>
        </div>

        <div class="nav-section">
          <span class="section-title" *ngIf="isOpen">ANALYTICS</span>
          <a
            *ngFor="let item of analyticsMenu"
            [routerLink]="item.route"
            routerLinkActive="active"
            class="nav-item"
            [title]="item.label"
          >
            <span class="nav-icon" [innerHTML]="safeSvg(item.iconSvg)"></span>
            <span class="nav-label" *ngIf="isOpen">{{ item.label }}</span>
            <span class="nav-badge" *ngIf="item.badge && isOpen">{{ item.badge }}</span>
          </a>
        </div>

        <div class="nav-section">
          <span class="section-title" *ngIf="isOpen">SYSTEM</span>
          <a
            *ngFor="let item of systemMenu"
            [routerLink]="item.route"
            routerLinkActive="active"
            class="nav-item"
            [title]="item.label"
          >
            <span class="nav-icon" [innerHTML]="safeSvg(item.iconSvg)"></span>
            <span class="nav-label" *ngIf="isOpen">{{ item.label }}</span>
            <span class="nav-badge" *ngIf="item.badge && isOpen">{{ item.badge }}</span>
          </a>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="status-indicator" *ngIf="isOpen">
          <span class="status-dot"></span>
          <span class="status-text">Connected</span>
        </div>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      width: 280px;
      background: linear-gradient(180deg, var(--vox-surface) 0%, var(--vox-dark) 100%);
      border-right: 1px solid var(--vox-border);
      display: flex;
      flex-direction: column;
      height: 100vh;
      transition: width 200ms ease-in-out;
      box-shadow: var(--shadow-xl);
      z-index: 1000;
      overflow: hidden;
    }

    .sidebar.collapsed { width: 80px; }

    @media (max-width: 1024px) {
      .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        height: 100vh;
        box-shadow: var(--shadow-2xl);
        transform: translateX(0);
        transition: transform 200ms ease-in-out, width 200ms ease-in-out;
      }
      .sidebar.collapsed { transform: translateX(-100%); }
    }

    .sidebar-header {
      padding: var(--spacing-xl) var(--spacing-lg);
      border-bottom: 1px solid var(--vox-border);
      background: linear-gradient(180deg, rgba(255, 140, 66, 0.05) 0%, transparent 100%);
    }

    .logo-container {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      cursor: pointer;
    }

    .logo-image {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-lg);
      background: var(--vox-surface-light);
      padding: var(--spacing-sm);
      transition: all var(--transition-base);
      flex-shrink: 0;
    }

    .logo-image:hover { box-shadow: var(--shadow-glow); transform: scale(1.05); }

    .logo-text {
      font-size: var(--font-size-lg);
      font-weight: 700;
      background: linear-gradient(135deg, var(--vox-orange) 0%, var(--vox-purple) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 1px;
      white-space: nowrap;
    }

    .sidebar-nav {
      flex: 1;
      overflow-y: auto;
      padding: var(--spacing-lg) 0;
    }

    .nav-section { margin-bottom: var(--spacing-xl); }

    .section-title {
      display: block;
      padding: 0 var(--spacing-lg);
      font-size: var(--font-size-xs);
      font-weight: 600;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: var(--spacing-md);
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-md) var(--spacing-lg);
      color: rgba(255, 255, 255, 0.7);
      transition: all var(--transition-base);
      position: relative;
      margin: 0 var(--spacing-md);
      border-radius: var(--radius-lg);
      white-space: nowrap;
      overflow: hidden;
      text-decoration: none;
    }

    .nav-item:hover {
      color: var(--vox-white);
      background: rgba(255, 140, 66, 0.1);
    }

    .nav-item.active {
      color: var(--vox-white);
      background: linear-gradient(90deg, rgba(255, 140, 66, 0.2) 0%, rgba(124, 58, 237, 0.1) 100%);
      border-left: 3px solid var(--vox-orange);
      font-weight: 600;
    }

    .nav-icon {
      width: 20px;
      height: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      color: rgba(255, 255, 255, 0.5);
      transition: all var(--transition-base);
    }

    .nav-item:hover .nav-icon,
    .nav-item.active .nav-icon { color: var(--vox-orange); }

    .nav-label {
      flex: 1;
      font-size: var(--font-size-sm);
      font-weight: 500;
    }

    .nav-badge {
      display: inline-block;
      background: var(--vox-orange);
      color: var(--vox-black);
      font-size: var(--font-size-xs);
      font-weight: 600;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      flex-shrink: 0;
    }

    .sidebar-footer {
      padding: var(--spacing-lg);
      border-top: 1px solid var(--vox-border);
      margin-top: auto;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-md);
      background: rgba(16, 185, 129, 0.1);
      border-radius: var(--radius-lg);
      border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      background: var(--vox-success);
      border-radius: 50%;
      animation: pulse 2s ease-in-out infinite;
      flex-shrink: 0;
    }

    .status-text {
      font-size: var(--font-size-sm);
      color: rgba(16, 185, 129, 0.8);
      font-weight: 500;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `],
})
export class SidebarComponent {
  private iconRender = inject(IconRenderService);

  @Input() isOpen = true;
  @Output() toggleSidebar = new EventEmitter<void>();

  safeSvg(svg: string): SafeHtml {
    return this.iconRender.renderSvg(svg);
  }

  private svg(path: string) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
  }

  mainMenu: MenuItem[] = [
    {
      label: 'Dashboard', route: '/dashboard',
      iconSvg: this.svg('<rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect>'),
    },
    {
      label: 'Artists', route: '/artists',
      iconSvg: this.svg('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>'),
    },
    {
      label: 'Tracks', route: '/tracks',
      iconSvg: this.svg('<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>'),
    },
    {
      label: 'Genres', route: '/genres',
      iconSvg: this.svg('<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line>'),
    },
    {
      label: 'Audio Features', route: '/audio-features',
      iconSvg: this.svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>'),
    },
  ];

  analyticsMenu: MenuItem[] = [
    {
      label: 'Trending', route: '/trending',
      iconSvg: this.svg('<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline>'),
    },
    {
      label: 'Analytics', route: '/analytics',
      iconSvg: this.svg('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>'),
    },
    {
      label: 'Comparatives', route: '/comparatives',
      iconSvg: this.svg('<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>'),
    },
  ];

  systemMenu: MenuItem[] = [
    {
      label: 'Pipeline ELT', route: '/elt-pipeline',
      iconSvg: this.svg('<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>'),
    },
    {
      label: 'Data Explorer', route: '/explorer',
      iconSvg: this.svg('<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>'),
    },
    {
      label: 'Settings', route: '/settings',
      iconSvg: this.svg('<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>'),
    },
  ];
}
