/**
 * LoginComponent — VOXMETRIK auth (login + register)
 */

import { Component, inject, signal, OnInit, NgZone, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
} from '@angular/forms';

import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { UiPreferencesService, AppLanguage } from '../../core/services/ui-preferences.service';
import { homePathForRole } from '../../core/navigation/nav-access.policy';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { BrandMarkComponent } from '../../shared/components/brand-mark/brand-mark.component';

type AuthMode = 'login' | 'register' | 'verify' | 'forgot' | 'reset';

declare global {
  interface Window {
    // Google Identity Services is loaded at runtime; keep a loose type here.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google?: any;
    onGoogleLibraryLoad?: () => void;
  }
}

const GIS_SCRIPT_ID = 'google-identity-services';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, TranslatePipe, BrandMarkComponent],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly i18n = inject(I18nService);
  private readonly ui = inject(UiPreferencesService);
  private readonly zone = inject(NgZone);

  protected readonly language = this.ui.language;

  protected readonly mode = signal<AuthMode>('login');
  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly showPassword = signal(false);

  // Email verification
  protected readonly pendingEmail = signal('');
  protected readonly devCode = signal('');
  protected readonly infoMessage = signal('');
  protected readonly resendCountdown = signal(0);
  private resendTimer: ReturnType<typeof setInterval> | null = null;

  // Google Sign-In
  protected readonly googleClientId = signal('');
  protected readonly googleReady = signal(false);
  private googleScriptLoading = false;

  protected readonly loginForm = this.fb.group({
    loginId: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(4)]],
    remember: [true],
  });

  protected readonly registerForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(4)]],
    favoriteGenre: ['Pop'],
  });

  protected readonly verifyForm = this.fb.group({
    code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]],
  });

  protected readonly forgotForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
  });

  protected readonly resetForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    code: ['', [Validators.required, Validators.minLength(6)]],
    newPassword: ['', [Validators.required, Validators.minLength(4)]],
  });

  ngOnInit(): void {
    this.auth.getAuthConfig().then((cfg) => {
      if (cfg?.google_client_id) {
        this.googleClientId.set(cfg.google_client_id);
        this.loadGoogleScript();
      }
    }).catch((err) => console.error('[LoginComponent] getAuthConfig failed', err));

    // Deep-link: /login?mode=reset&email=...
    const params = new URLSearchParams(window.location.search);
    const mode = params.get('mode');
    const email = params.get('email');
    if (mode === 'reset') {
      this.setMode('reset');
      if (email) this.resetForm.patchValue({ email });
    } else if (mode === 'forgot') {
      this.setMode('forgot');
    }
  }

  protected setLanguage(lang: AppLanguage): void {
    this.ui.setLanguage(lang);
  }

  protected setMode(m: AuthMode): void {
    this.mode.set(m);
    this.errorMessage.set('');
    this.infoMessage.set('');
  }

  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  protected onLoginSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }
    this.isLoading.set(true);
    this.errorMessage.set('');
    const { loginId, password, remember } = this.loginForm.getRawValue();
    this.auth.login(loginId!, password!, remember ?? true).then((res) => {
      if (res.ok) {
        void this.router.navigateByUrl(homePathForRole(this.auth.role()));
        return;
      }
      this.isLoading.set(false);
      if (res.verificationRequired && res.email) {
        this.pendingEmail.set(res.email);
        this.infoMessage.set(this.i18n.t('verify.needed'));
        this.setMode('verify');
      } else {
        this.errorMessage.set(this.i18n.t('login.invalidCredentials'));
      }
    });
  }

  protected onRegisterSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }
    this.isLoading.set(true);
    this.errorMessage.set('');
    const { username, email, password, favoriteGenre } = this.registerForm.getRawValue();
    this.auth.register(username!, email!, password!, favoriteGenre || undefined).then((res) => {
      this.isLoading.set(false);
      if (res.ok && res.verificationRequired) {
        this.pendingEmail.set(res.email ?? email!);
        this.devCode.set(res.devCode ?? '');
        this.setMode('verify');
        this.infoMessage.set(this.i18n.t('verify.sent'));
        this.startResendCountdown(60);
      } else if (res.ok) {
        void this.router.navigateByUrl(homePathForRole(this.auth.role()));
      } else {
        this.errorMessage.set(res.error ?? this.i18n.t('login.registerError'));
      }
    });
  }

  protected onVerifySubmit(): void {
    if (this.verifyForm.invalid) {
      this.verifyForm.markAllAsTouched();
      return;
    }
    this.isLoading.set(true);
    this.errorMessage.set('');
    const code = this.verifyForm.getRawValue().code!;
    this.auth.verifyEmail(this.pendingEmail(), code).then((res) => {
      if (res.ok) {
        void this.router.navigateByUrl(homePathForRole(this.auth.role()));
      } else {
        this.isLoading.set(false);
        this.errorMessage.set(res.error ?? this.i18n.t('verify.invalid'));
      }
    });
  }

  protected onResendCode(): void {
    if (this.resendCountdown() > 0) return;
    this.errorMessage.set('');
    this.infoMessage.set('');
    this.auth.resendCode(this.pendingEmail()).then((res) => {
      if (res.ok) {
        this.devCode.set(res.devCode ?? '');
        this.infoMessage.set(this.i18n.t('verify.resent'));
        this.startResendCountdown(res.retryAfterSec ?? 60);
      } else {
        this.errorMessage.set(res.error ?? this.i18n.t('verify.resendError'));
      }
    });
  }

  protected onForgotSubmit(): void {
    if (this.forgotForm.invalid) {
      this.forgotForm.markAllAsTouched();
      return;
    }
    this.isLoading.set(true);
    this.errorMessage.set('');
    const email = this.forgotForm.getRawValue().email!;
    this.auth.forgotPassword(email).then((res) => {
      this.isLoading.set(false);
      this.infoMessage.set(res.message ?? this.i18n.t('reset.generic'));
      this.devCode.set(res.devCode ?? '');
      this.resetForm.patchValue({ email });
      this.setMode('reset');
    });
  }

  protected onResetSubmit(): void {
    if (this.resetForm.invalid) {
      this.resetForm.markAllAsTouched();
      return;
    }
    this.isLoading.set(true);
    this.errorMessage.set('');
    const { email, code, newPassword } = this.resetForm.getRawValue();
    this.auth.resetPassword(email!, code!, newPassword!).then((res) => {
      this.isLoading.set(false);
      if (res.ok) {
        this.infoMessage.set(this.i18n.t('reset.success'));
        this.setMode('login');
      } else {
        this.errorMessage.set(res.error ?? this.i18n.t('reset.error'));
      }
    });
  }

  private startResendCountdown(seconds: number): void {
    if (this.resendTimer) clearInterval(this.resendTimer);
    this.resendCountdown.set(seconds);
    this.resendTimer = setInterval(() => {
      const next = this.resendCountdown() - 1;
      if (next <= 0) {
        this.resendCountdown.set(0);
        if (this.resendTimer) clearInterval(this.resendTimer);
        this.resendTimer = null;
      } else {
        this.resendCountdown.set(next);
      }
    }, 1000);
  }

  // ── Google Sign-In ─────────────────────────────────────────────
  private googleHost?: HTMLElement;

  @ViewChild('googleBtn') set googleBtn(el: ElementRef<HTMLElement> | undefined) {
    this.googleHost = el?.nativeElement;
    this.renderGoogleButton();
  }

  private loadGoogleScript(): void {
    if (window.google?.accounts?.id) {
      this.onGoogleLoaded();
      return;
    }
    if (this.googleScriptLoading || document.getElementById(GIS_SCRIPT_ID)) return;
    this.googleScriptLoading = true;
    const script = document.createElement('script');
    script.id = GIS_SCRIPT_ID;
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => this.zone.run(() => this.onGoogleLoaded());
    document.head.appendChild(script);
  }

  private onGoogleLoaded(): void {
    const clientId = this.googleClientId();
    if (!clientId || !window.google?.accounts?.id) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (resp: { credential: string }) => this.handleGoogleCredential(resp),
    });
    this.googleReady.set(true);
    this.renderGoogleButton();
  }

  private renderGoogleButton(): void {
    if (!this.googleReady() || !this.googleHost || !window.google?.accounts?.id) return;
    this.googleHost.innerHTML = '';
    window.google.accounts.id.renderButton(this.googleHost, {
      theme: 'outline',
      size: 'large',
      width: 320,
      text: 'continue_with',
      logo_alignment: 'center',
    });
  }

  private handleGoogleCredential(resp: { credential: string }): void {
    if (!resp?.credential) return;
    this.zone.run(() => {
      this.isLoading.set(true);
      this.errorMessage.set('');
      this.auth.loginWithGoogle(resp.credential).then((ok) => {
        if (ok) {
          void this.router.navigateByUrl(homePathForRole(this.auth.role()));
        } else {
          this.isLoading.set(false);
          this.errorMessage.set(this.i18n.t('login.googleError'));
        }
      });
    });
  }
}
