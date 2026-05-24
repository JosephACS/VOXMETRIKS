import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <header class="header">
      <div class="header-left">
        <button class="menu-toggle" (click)="onToggleSidebar()">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
               fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <div class="breadcrumb">
          <span class="breadcrumb-item">Dashboard</span>
        </div>
      </div>

      <div class="header-center">
        <div class="search-box">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
               fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" placeholder="Search tracks, artists, genres..." />
        </div>
      </div>

      <div class="header-right">
        <div class="header-badge">
          <span class="badge-dot"></span>
          <span class="badge-text">Live</span>
        </div>
        <button class="avatar-btn">
          <div class="avatar">V</div>
        </button>
      </div>
    </header>
  `,
  styles: [`
    .header {
      background: linear-gradient(90deg, var(--vox-surface) 0%, var(--vox-surface-light) 100%);
      border-bottom: 1px solid var(--vox-border);
      padding: 0 var(--spacing-xl);
      height: 70px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--spacing-xl);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    @media (max-width: 768px) {
      .header { padding: 0 var(--spacing-lg); height: 60px; }
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: var(--spacing-lg);
      flex: 0 0 auto;
    }

    .menu-toggle {
      background: none;
      border: none;
      color: var(--vox-white);
      cursor: pointer;
      display: none;
      padding: var(--spacing-sm);
      border-radius: var(--radius-md);
      transition: all var(--transition-base);
    }

    .menu-toggle:hover {
      background: rgba(255, 140, 66, 0.1);
      color: var(--vox-orange);
    }

    @media (max-width: 1024px) {
      .menu-toggle { display: flex; align-items: center; justify-content: center; }
    }

    .breadcrumb {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      font-size: var(--font-size-sm);
    }

    .breadcrumb-item {
      color: rgba(255, 255, 255, 0.7);
      font-weight: 500;
    }

    .header-center {
      flex: 1;
      max-width: 500px;
      display: flex;
      justify-content: center;
    }

    @media (max-width: 1024px) {
      .header-center { display: none; }
    }

    .search-box {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: 0 var(--spacing-lg);
      background: var(--vox-surface-light);
      border: 1px solid var(--vox-border);
      border-radius: var(--radius-lg);
      width: 100%;
      height: 40px;
      transition: all var(--transition-base);
      color: rgba(255, 255, 255, 0.5);
    }

    .search-box:focus-within {
      border-color: var(--vox-orange);
      background: var(--vox-surface);
      box-shadow: 0 0 0 2px rgba(255, 140, 66, 0.1);
    }

    .search-box svg { flex-shrink: 0; }

    .search-box input {
      border: none;
      background: transparent;
      color: var(--vox-white);
      font-size: var(--font-size-sm);
      width: 100%;
      outline: none;
    }

    .search-box input::placeholder { color: rgba(255, 255, 255, 0.4); }

    .header-right {
      display: flex;
      align-items: center;
      gap: var(--spacing-lg);
      flex: 0 0 auto;
    }

    .header-badge {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: 6px 12px;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: var(--radius-md);
      font-size: var(--font-size-xs);
      font-weight: 600;
      color: var(--vox-success);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    @media (max-width: 768px) { .header-badge { display: none; } }

    .badge-dot {
      width: 6px;
      height: 6px;
      background: var(--vox-success);
      border-radius: 50%;
      animation: pulse 2s ease-in-out infinite;
    }

    .avatar-btn {
      background: none;
      border: none;
      cursor: pointer;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-lg);
      background: linear-gradient(135deg, var(--vox-orange) 0%, var(--vox-purple) 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--vox-black);
      font-weight: 700;
      font-size: var(--font-size-lg);
      transition: all var(--transition-base);
      cursor: pointer;
    }

    .avatar:hover {
      box-shadow: var(--shadow-glow);
      transform: scale(1.05);
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `],
})
export class HeaderComponent {
  @Output() toggleSidebar = new EventEmitter<void>();

  onToggleSidebar() {
    this.toggleSidebar.emit();
  }
}
