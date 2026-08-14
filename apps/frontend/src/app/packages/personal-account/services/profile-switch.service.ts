import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { SessionCleanupCoordinator } from '../../../core/spaces/session-cleanup.coordinator';
import { PersonalAccountApiService } from './personal-account-api.service';
import { SecurityApiService } from './security-api.service';
import { AuthResponse } from '../../../shared/models/api.models';

const ASK_KEY = 'voxmetriks_ask_who_listening';
const REMEMBER_PREFIX = 'voxmetriks_remember_profile_';
const SESSION_SELECTED_KEY = 'voxmetriks_profile_session_selected';

/**
 * Secure profile switch: never impersonates.
 * Clears the current session and opens login with a suggested login id only.
 */
@Injectable({ providedIn: 'root' })
export class ProfileSwitchService {
  private auth = inject(AuthService);
  private router = inject(Router);
  private cleanup = inject(SessionCleanupCoordinator);
  private personalApi = inject(PersonalAccountApiService);
  private securityApi = inject(SecurityApiService);

  private rememberKey(userId: number): string {
    return `${REMEMBER_PREFIX}${userId}`;
  }

  isAskWhoListeningEnabled(): boolean {
    try {
      const v = localStorage.getItem(ASK_KEY);
      // Default ON when unset.
      return v !== '0';
    } catch {
      return true;
    }
  }

  setAskWhoListening(on: boolean): void {
    try {
      localStorage.setItem(ASK_KEY, on ? '1' : '0');
    } catch {
      /* ignore */
    }
  }

  isRememberProfile(userId?: number | null): boolean {
    const id = userId ?? this.auth.getUser()?.id;
    if (id == null) return false;
    try {
      return localStorage.getItem(this.rememberKey(id)) === '1';
    } catch {
      return false;
    }
  }

  setRememberProfile(on: boolean, userId?: number | null): void {
    const id = userId ?? this.auth.getUser()?.id;
    if (id == null) return;
    try {
      if (on) localStorage.setItem(this.rememberKey(id), '1');
      else localStorage.removeItem(this.rememberKey(id));
    } catch {
      /* ignore */
    }
  }

  markSessionSelected(userId?: number | null): void {
    const id = userId ?? this.auth.getUser()?.id;
    if (id == null) return;
    try {
      sessionStorage.setItem(SESSION_SELECTED_KEY, String(id));
    } catch {
      /* ignore */
    }
  }

  clearSessionSelected(): void {
    try {
      sessionStorage.removeItem(SESSION_SELECTED_KEY);
    } catch {
      /* ignore */
    }
  }

  wasSelectedThisSession(userId?: number | null): boolean {
    const id = userId ?? this.auth.getUser()?.id;
    if (id == null) return false;
    try {
      return sessionStorage.getItem(SESSION_SELECTED_KEY) === String(id);
    } catch {
      return false;
    }
  }

  /** Legacy alias used by older UI — maps to ask-who-listening inverted shared-device. */
  isSharedDevice(): boolean {
    return this.isAskWhoListeningEnabled();
  }

  setSharedDevice(on: boolean): void {
    this.setAskWhoListening(on);
  }

  markContinueAsMe(remember = false): void {
    const id = this.auth.getUser()?.id;
    this.markSessionSelected(id);
    if (remember) this.setRememberProfile(true, id);
  }

  shouldPromptSelector(memberCount: number, userId?: number | null): boolean {
    if (memberCount <= 1) return false;
    if (!this.isAskWhoListeningEnabled()) return false;
    const id = userId ?? this.auth.getUser()?.id ?? null;
    if (this.isRememberProfile(id)) return false;
    if (this.wasSelectedThisSession(id)) return false;
    return true;
  }

  /**
   * After login: route to profile selector when Duo/Familiar has 2+ members.
   * Returns the path navigated to.
   */
  async resolvePostLoginDestination(fallback = '/discover'): Promise<string> {
    const userId = this.auth.getUser()?.id ?? null;
    try {
      const res = await firstValueFrom(this.personalApi.getProfiles());
      const count = res?.profiles?.length ?? 0;
      const show = !!res?.show_selector && count > 1;
      if (!show) {
        this.markSessionSelected(userId);
        return fallback;
      }
      if (!this.shouldPromptSelector(count, userId)) {
        this.markSessionSelected(userId);
        return fallback;
      }
      return '/account/profiles';
    } catch {
      return fallback;
    }
  }

  clearPrivateClientState(): void {
    // Single implementation so profile switch, logout and 401 clear the same state.
    this.cleanup.clearPrivateClientState();
  }

  /** Logout safely and open login with optional suggested username (never password). */
  switchToLoginHint(loginHint?: string | null): void {
    this.clearPrivateClientState();
    this.auth.logout();
    const hint = (loginHint || '').trim();
    void this.router.navigate(['/login'], {
      queryParams: hint ? { login: hint } : {},
    });
  }

  async prepareAndSwitch(targetUserId: number): Promise<void> {
    // Authorize switch intent, then force manual reauth with no preloaded identity.
    await firstValueFrom(this.personalApi.prepareProfileSwitch(targetUserId));
    this.switchToLoginHint(null);
  }

  /**
   * Try switching to another household member via PIN + trusted device token.
   * Returns password_required when the device is not authorized for that profile.
   */
  async tryPinUnlockSwitch(
    targetUserId: number,
    pin: string,
    deviceToken: string,
  ): Promise<'ok' | 'password_required' | 'error'> {
    try {
      const res = await firstValueFrom(
        this.securityApi.unlockPinSwitch({
          target_user_id: targetUserId,
          pin,
          device_token: deviceToken,
        }),
      );
      if ('token' in res && 'user' in res) {
        this.clearPrivateClientState();
        this.auth.applySession(res as AuthResponse, true);
        this.markContinueAsMe(false);
        return 'ok';
      }
      return 'ok';
    } catch (err: unknown) {
      const code = SecurityApiService.errorCode(err);
      if (code === 'device_required' || code === 'forbidden') {
        return 'password_required';
      }
      return 'error';
    }
  }
}
