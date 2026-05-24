import { Injectable, signal } from '@angular/core';

export interface AuthState {
  isAuthenticated: boolean;
  user: { username: string } | null;
  token: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly AUTH_KEY = 'voxmetrik_auth_token';
  private readonly USER_KEY = 'voxmetrik_user';

  // Signals para estado reactivo
  protected authState = signal<AuthState>({
    isAuthenticated: this.hasToken(),
    user: this.getStoredUser(),
    token: this.getStoredToken(),
  });

  // Getters públicos como signals
  isAuthenticated = () => this.authState().isAuthenticated;
  getToken = () => this.authState().token;
  getUser = () => this.authState().user;

  constructor() {
    // Sincronizar con localStorage al iniciar
    this.syncFromStorage();
  }

  /**
   * Login simulado — reemplazar con PocketBase en el futuro
   */
  login(username: string, password: string): Promise<boolean> {
    return new Promise((resolve) => {
      // Simulación: cualquier credencial funciona
      const mockToken = `mock-token-${Date.now()}`;
      const user = { username };

      localStorage.setItem(this.AUTH_KEY, mockToken);
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));

      this.authState.set({
        isAuthenticated: true,
        user,
        token: mockToken,
      });

      resolve(true);
    });
  }

  /**
   * Logout — limpia estado y storage
   */
  logout(): void {
    localStorage.removeItem(this.AUTH_KEY);
    localStorage.removeItem(this.USER_KEY);

    this.authState.set({
      isAuthenticated: false,
      user: null,
      token: null,
    });
  }

  /**
   * Sincronizar estado con localStorage al iniciar
   */
  private syncFromStorage(): void {
    const token = this.getStoredToken();
    const user = this.getStoredUser();

    if (token) {
      this.authState.set({
        isAuthenticated: true,
        user,
        token,
      });
    }
  }

  /**
   * Obtener token de localStorage
   */
  private getStoredToken(): string | null {
    return localStorage.getItem(this.AUTH_KEY);
  }

  /**
   * Obtener usuario de localStorage
   */
  private getStoredUser(): { username: string } | null {
    const stored = localStorage.getItem(this.USER_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  }

  /**
   * Verificar si hay token válido
   */
  private hasToken(): boolean {
    return !!localStorage.getItem(this.AUTH_KEY);
  }
}
