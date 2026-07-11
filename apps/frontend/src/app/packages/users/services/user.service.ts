import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  UserProfile, UserPublic, UserPreferencesUpdate,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/users`;

  profile = signal<UserProfile | null>(null);

  getMe(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.API}/me`).pipe(
      tap((p) => this.profile.set(p))
    );
  }

  updatePreferences(body: UserPreferencesUpdate): Observable<UserPublic> {
    return this.http.patch<UserPublic>(`${this.API}/me/preferences`, body).pipe(
      tap((u) => {
        const cur = this.profile();
        if (cur) {
          this.profile.set({
            ...cur,
            ...u,
            preferences: u.preferences ?? cur.preferences,
          });
        }
      })
    );
  }
}
