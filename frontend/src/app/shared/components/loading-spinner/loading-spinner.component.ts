import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoadingService } from '../../services/loading.service';
import { Observable } from 'rxjs';

/** Indicador de carga inicial — barra superior, sin bloquear la UI. */
@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (isLoading$ | async) {
      <div class="loader-bar-track" aria-hidden="true">
        <div class="loader-bar-fill"></div>
      </div>
    }
  `,
  styles: [`
    .loader-bar-track {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      z-index: 9999;
      background: rgba(255, 255, 255, 0.04);
      overflow: hidden;
      pointer-events: none;
    }

    .loader-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--accent, #1ed896), #148f5e);
      animation: loader-slide 1.2s cubic-bezier(0.22, 1, 0.36, 1) infinite;
      box-shadow: 0 0 12px rgba(30, 216, 150, 0.45);
    }

    @keyframes loader-slide {
      0% { width: 0; margin-left: 0; opacity: 0.6; }
      50% { width: 55%; margin-left: 22%; opacity: 1; }
      100% { width: 0; margin-left: 100%; opacity: 0.6; }
    }

    @media (max-width: 640px) {
      .loader-bar-track { height: 3px; }
    }
  `],
})
export class LoadingSpinnerComponent {
  isLoading$: Observable<boolean>;

  constructor(private loadingService: LoadingService) {
    this.isLoading$ = this.loadingService.isLoading$;
  }
}
