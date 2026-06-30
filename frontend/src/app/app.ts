import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { UiPreferencesService } from './core/services/ui-preferences.service';
import { I18nService } from './core/services/i18n.service';
import { ConfirmDialogComponent } from './shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ConfirmDialogComponent],
  template: `
    <router-outlet></router-outlet>
    <app-confirm-dialog />
  `,
})
export class App {
  title = 'VOXMETRIK';
  private readonly _ui = inject(UiPreferencesService);
  private readonly _i18n = inject(I18nService);
}
