import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LoadingSpinnerComponent } from './shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, LoadingSpinnerComponent],
  template: `
    <app-loading-spinner></app-loading-spinner>
    <router-outlet></router-outlet>
  `,
})
export class App {
  title = 'VOXMETRIK';
}
