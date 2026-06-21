import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AppUser, AuthResponse } from '../../shared/models/api.models';
import { UiPreferencesService } from './ui-preferences.service';

export interface AuthState {
  isAuthenticated: boolean;
  user: AppUser | null;
  token: string | null;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly ui = inject(UiPreferencesService);
  private readonly API = `${environment.apiUrl}/users`;
  private readonly AUTH_KEY = 'voxmetrik_auth_token';
  private readonly USER_KEY = 'voxmetrik_user';

  private authState = signal<AuthState>({
    isAuthenticated: this.hasToken(),
    user: this.getStoredUser(),
    token: this.getStoredToken(),
  });

  readonly state = this.authState.asReadonly();
  isAuthenticated = () => this.authState().isAuthenticated;
  getToken = () => this.authState().token;
  getUser = () => this.authState().user;
  userId = computed(() => this.authState().user?.id ?? null);

  /** Acceso a ingeniería de datos (Pipeline ELT, Explorer). Usuario admin en demo. */
  hasEngineerAccess(): boolean {
    const u = this.getUser();
    if (!u) return false;
    const email = (u.email ?? '').toLowerCase();
    const username = (u.username ?? '').toLowerCase();
    return username === 'admin' || email.startsWith('admin@');
  }

  constructor() {
    this.syncFromStorage();
  }

  async login(loginId: string, password: string, remember = true): Promise<boolean> {
    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(`${this.API}/login`, {
          login: loginId.trim(),
          password,
          remember,
        })
      );
      this.persistSession(res, remember);
      return true;
    } catch {
      return false;
    }
  }

  async register(
    username: string,
    email: string,
    password: string,
    favoriteGenre?: string,
  ): Promise<{ ok: boolean; error?: string }> {
    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(`${this.API}/register`, {
          username,
          email,
          password,
          favorite_genre: favoriteGenre,
        })
      );
      this.persistSession(res, true);
      return { ok: true };
    } catch (e: unknown) {
      const err = e as { error?: { detail?: string } };
      return { ok: false, error: err?.error?.detail ?? 'Error al registrar' };
    }
  }

  logout(): void {
    localStorage.removeItem(this.AUTH_KEY);
    localStorage.removeItem(this.USER_KEY);
    sessionStorage.removeItem(this.AUTH_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    this.authState.set({ isAuthenticated: false, user: null, token: null });
  }

  private persistSession(res: AuthResponse, remember: boolean): void {
    const store = remember ? localStorage : sessionStorage;
    const other = remember ? sessionStorage : localStorage;
    other.removeItem(this.AUTH_KEY);
    other.removeItem(this.USER_KEY);
    store.setItem(this.AUTH_KEY, res.token);
    store.setItem(this.USER_KEY, JSON.stringify(res.user));
    this.authState.set({
      isAuthenticated: true,
      user: res.user,
      token: res.token,
    });
    if (res.user.preferences?.dark_mode != null) {
      this.ui.syncThemeFromDarkMode(res.user.preferences.dark_mode);
    }
  }

  private syncFromStorage(): void {
    const token = this.getStoredToken();
    const user = this.getStoredUser();
    if (token && user) {
      this.authState.set({ isAuthenticated: true, user, token });
      if (user.preferences?.dark_mode != null) {
        this.ui.syncThemeFromDarkMode(user.preferences.dark_mode);
      }
    }
  }

  getStoredToken(): string | null {
    return localStorage.getItem(this.AUTH_KEY) ?? sessionStorage.getItem(this.AUTH_KEY);
  }

  private getStoredUser(): AppUser | null {
    const raw =
      localStorage.getItem(this.USER_KEY) ?? sessionStorage.getItem(this.USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AppUser;
    } catch {
      return null;
    }
  }

  private hasToken(): boolean {
    return !!this.getStoredToken();
  }
}
