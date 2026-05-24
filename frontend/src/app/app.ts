import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { UiPreferencesService } from './core/services/ui-preferences.service';
import { I18nService } from './core/services/i18n.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet></router-outlet>`,
})
export class App {
  title = 'VOXMETRIK';
  private readonly _ui = inject(UiPreferencesService);
  private readonly _i18n = inject(I18nService);
}
