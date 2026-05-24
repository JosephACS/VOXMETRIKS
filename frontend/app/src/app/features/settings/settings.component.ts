import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h1>Settings</h1>
      <p>Application preferences</p>
    </div>
    <div class="settings-container">
      <div class="setting-item">
        <h4>Theme</h4>
        <select class="setting-select">
          <option>Dark Mode</option>
          <option>Light Mode</option>
        </select>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 2rem; }
    .settings-container { background: var(--vox-surface); border: 1px solid var(--vox-border); border-radius: 0.75rem; padding: 2rem; }
    .setting-item { margin-bottom: 2rem; }
    .setting-item h4 { margin-top: 0; }
    .setting-select { background: var(--vox-surface-light); border: 1px solid var(--vox-border); color: white; padding: 0.75rem; border-radius: 0.5rem; width: 200px; }
  `]
})
export class SettingsComponent {}
