import { Injectable, signal, computed } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly _count = signal(0);
  readonly isLoading = computed(() => this._count() > 0);
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public isLoading$: Observable<boolean> = this.loadingSubject.asObservable();

  startLoading(): void { this._count.update(n => n + 1); this.loadingSubject.next(true); }
  stopLoading(): void  { this._count.update(n => Math.max(0, n - 1)); if (this._count() === 0) this.loadingSubject.next(false); }
  show(): void { this.startLoading(); }
  hide(): void { this.stopLoading(); }
  reset(): void { this._count.set(0); this.loadingSubject.next(false); }
}
