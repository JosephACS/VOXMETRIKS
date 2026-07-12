import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AppUser, AuthResponse, AuthConfig } from '../../shared/models/api.models';
import { UiPreferencesService } from './ui-preferences.service';

export interface AuthState {
  isAuthenticated: boolean;
  user: AppUser | null;
  token: string | null;
}

export interface LoginResult {
  ok: boolean;
  verificationRequired?: boolean;
  email?: string;
}

export interface RegisterResult {
  ok: boolean;
  verificationRequired?: boolean;
  email?: string;
  devCode?: string;
  error?: string;
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

  /** Current normalized role. */
  readonly role = computed(() => (this.authState().user?.role ?? 'user').toLowerCase());

  /**
   * Catalog steward = ONLY the administrator can create/edit/delete artists,
   * tracks and genres. Data engineers manage the ELT pipeline + analytics, but
   * never mutate the catalog by hand. Mirrors backend require_admin_user.
   */
  readonly isCatalogSteward = computed(() => this.role() === 'admin');

  /** True for the administrator. */
  readonly isAdmin = computed(() => this.role() === 'admin');

  /**
   * Engineering access = admin OR data engineer. Gates the ELT pipeline and
   * analytics-only routes (engineerGuard), NOT the catalog CRUD.
   */
  hasEngineerAccess(): boolean {
    const r = this.role();
    return r === 'admin' || r === 'engineer';
  }

  constructor() {
    this.syncFromStorage();
  }

  async login(loginId: string, password: string, remember = true): Promise<LoginResult> {
    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(`${this.API}/login`, {
          login: loginId.trim(),
          password,
          remember,
        })
      );
      this.persistSession(res, remember);
      return { ok: true };
    } catch (e: unknown) {
      const err = e as { status?: number; error?: { detail?: { reason?: string; email?: string } | string } };
      const detail = err?.error?.detail;
      if (err?.status === 403 && typeof detail === 'object' && detail?.reason === 'email_not_verified') {
        return { ok: false, verificationRequired: true, email: detail.email };
      }
      return { ok: false };
    }
  }

  async register(
    username: string,
    email: string,
    password: string,
    favoriteGenre?: string,
  ): Promise<RegisterResult> {
    try {
      const res = await firstValueFrom(
        this.http.post<{ verification_required?: boolean; email?: string; dev_code?: string }>(
          `${this.API}/register`,
          { username, email, password, favorite_genre: favoriteGenre },
        )
      );
      return {
        ok: true,
        verificationRequired: !!res.verification_required,
        email: res.email ?? email,
        devCode: res.dev_code,
      };
    } catch (e: unknown) {
      const err = e as { error?: { detail?: string } };
      return { ok: false, error: err?.error?.detail ?? 'Error al registrar' };
    }
  }

  /** Confirm sign-up with the emailed code → persists the session on success. */
  async verifyEmail(email: string, code: string): Promise<{ ok: boolean; error?: string }> {
    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(`${this.API}/verify-email`, { email, code })
      );
      this.persistSession(res, true);
      return { ok: true };
    } catch (e: unknown) {
      const err = e as { error?: { detail?: string } };
      return { ok: false, error: err?.error?.detail ?? 'Código inválido' };
    }
  }

  async resendCode(email: string): Promise<{ ok: boolean; devCode?: string; retryAfterSec?: number; error?: string }> {
    try {
      const res = await firstValueFrom(
        this.http.post<{ dev_code?: string; rate_limited?: boolean; retry_after_sec?: number }>(
          `${this.API}/resend-code`,
          { email },
        )
      );
      return {
        ok: true,
        devCode: res.dev_code,
        retryAfterSec: res.retry_after_sec,
      };
    } catch (e: unknown) {
      const err = e as { error?: { detail?: string } };
      return { ok: false, error: err?.error?.detail ?? 'No se pudo reenviar el código' };
    }
  }

  async forgotPassword(email: string): Promise<{ ok: boolean; message?: string; devCode?: string }> {
    try {
      const res = await firstValueFrom(
        this.http.post<{ ok?: boolean; message?: string; dev_code?: string }>(
          `${this.API}/forgot-password`,
          { email },
        )
      );
      return { ok: true, message: res.message, devCode: res.dev_code };
    } catch {
      return { ok: true, message: 'If an account exists for that email, reset instructions were sent.' };
    }
  }

  async resetPassword(email: string, code: string, newPassword: string): Promise<{ ok: boolean; error?: string }> {
    try {
      await firstValueFrom(
        this.http.post(`${this.API}/reset-password`, {
          email,
          code,
          new_password: newPassword,
        })
      );
      return { ok: true };
    } catch (e: unknown) {
      const err = e as { error?: { detail?: string } };
      return { ok: false, error: err?.error?.detail ?? 'No se pudo restablecer la contraseña' };
    }
  }

  /** Sign in (or auto-register) with a Google ID token credential. */
  async loginWithGoogle(credential: string): Promise<boolean> {
    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(`${this.API}/google`, { credential })
      );
      this.persistSession(res, true);
      return true;
    } catch {
      return false;
    }
  }

  getAuthConfig(): Promise<AuthConfig> {
    return firstValueFrom(this.http.get<AuthConfig>(`${this.API}/auth-config`));
  }

  logout(): void {
    const token = this.getStoredToken();
    if (token) {
      void firstValueFrom(this.http.post(`${this.API}/logout`, {})).catch(() => undefined);
    }
    this.clearSession();
  }

  /** Drop local credentials without calling the server (e.g. after 401). */
  clearSession(): void {
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
