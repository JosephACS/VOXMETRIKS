import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { UiPreferencesService } from './core/services/ui-preferences.service';
import { I18nService } from './core/services/i18n.service';
import { ConfirmDialogComponent } from './shared/components/confirm-dialog/confirm-dialog.component';
import { NotificationToastComponent } from './shared/components/notification-toast/notification-toast.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ConfirmDialogComponent, NotificationToastComponent],
  template: `
    <router-outlet></router-outlet>
    @defer (on idle) {
      <app-confirm-dialog />
      <app-notification-toast />
    }
  `,
})
export class App {
  title = 'VOXMETRIKS';
  private readonly _ui = inject(UiPreferencesService);
  private readonly _i18n = inject(I18nService);
}
