import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { UserInsights } from '../models/enterprise-api.models';

@Injectable({ providedIn: 'root' })
export class EnterpriseUsersService {
  private readonly api = inject(ApiService);

  getUserInsights(userId: number): Observable<UserInsights> {
    return this.api.get<UserInsights>(`/users/${userId}/insights`);
  }
}
