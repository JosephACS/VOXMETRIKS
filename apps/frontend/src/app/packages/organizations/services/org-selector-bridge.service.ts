import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

/** Lets enterprise pages request opening the topbar org selector. */
@Injectable({ providedIn: 'root' })
export class OrgSelectorBridgeService {
  private readonly openRequested = new Subject<void>();
  readonly openRequests$ = this.openRequested.asObservable();

  requestOpen(): void {
    this.openRequested.next();
  }
}
