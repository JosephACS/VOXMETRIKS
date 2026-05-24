import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoadingService } from '../../services/loading.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="loader" *ngIf="(isLoading$ | async)" [@fadeInOut]>
      <div class="loader-container">
        <div class="loader-circle"></div>
        <div class="loader-text">VOXMETRIK</div>
      </div>
    </div>
  `,
  styles: [`
    .loader {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(10, 14, 39, 0.95);
      backdrop-filter: blur(5px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      animation: fadeIn 300ms ease-out;
    }

    .loader-container {
      position: relative;
      width: 120px;
      height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: var(--spacing-lg);
    }

    .loader-circle {
      width: 80px;
      height: 80px;
      border: 3px solid var(--vox-border);
      border-top-color: var(--vox-orange);
      border-right-color: var(--vox-purple);
      border-radius: 50%;
      animation: spin 1.5s linear infinite;
      box-shadow: 0 0 20px rgba(30, 216, 150, 0.2), 0 0 40px rgba(124, 58, 237, 0.1);
    }

    .loader-text {
      font-size: var(--font-size-sm);
      font-weight: 700;
      letter-spacing: 2px;
      background: linear-gradient(135deg, var(--vox-orange) 0%, var(--vox-purple) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: pulse 2s ease-in-out infinite;
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 0.6;
      }
      50% {
        opacity: 1;
      }
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }
  `],
})
export class LoadingSpinnerComponent {
  isLoading$: Observable<boolean>;

  constructor(private loadingService: LoadingService) {
    this.isLoading$ = this.loadingService.isLoading$;
  }
}
