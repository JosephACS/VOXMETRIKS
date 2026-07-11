/**
 * LoginComponent — VOXMETRIK auth (login + register)
 */

import { Component, inject, signal, OnInit, NgZone, ElementRef, ViewChild } from '@angular/core';
import { UpperCasePipe } from '@angular/common';
import { Router } from '@angular/router';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
} from '@angular/forms';

import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { UiPreferencesService, AppLanguage } from '../../core/services/ui-preferences.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { StatsService } from '../../packages/analytics/services/stats.service';
import { StatsSummary } from '../../shared/models/api.models';

type AuthMode = 'login' | 'register' | 'verify';

declare global {
  interface Window {
    google?: any;
    onGoogleLibraryLoad?: () => void;
  }
}

const GIS_SCRIPT_ID = 'google-identity-services';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, TranslatePipe, UpperCasePipe],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly stats = inject(StatsService);
  private readonly i18n = inject(I18nService);
  private readonly ui = inject(UiPreferencesService);
  private readonly zone = inject(NgZone);

  protected readonly language = this.ui.language;

  protected readonly mode = signal<AuthMode>('login');
  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly showPassword = signal(false);
  protected readonly summary = signal<StatsSummary | null>(null);

  // Email verification
  protected readonly pendingEmail = signal('');
  protected readonly devCode = signal('');
  protected readonly infoMessage = signal('');

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

  ngOnInit(): void {
    this.stats.getSummary().subscribe({
      next: (data) => this.summary.set(data),
      error: (err) => console.error('[LoginComponent] getSummary failed', err),
    });
    this.auth.getAuthConfig().then((cfg) => {
      if (cfg?.google_client_id) {
        this.googleClientId.set(cfg.google_client_id);
        this.loadGoogleScript();
      }
    }).catch((err) => console.error('[LoginComponent] getAuthConfig failed', err));
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
        this.router.navigate(['/discover']);
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
      } else if (res.ok) {
        this.router.navigate(['/discover']);
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
        this.router.navigate(['/discover']);
      } else {
        this.isLoading.set(false);
        this.errorMessage.set(res.error ?? this.i18n.t('verify.invalid'));
      }
    });
  }

  protected onResendCode(): void {
    this.errorMessage.set('');
    this.infoMessage.set('');
    this.auth.resendCode(this.pendingEmail()).then((res) => {
      if (res.ok) {
        this.devCode.set(res.devCode ?? '');
        this.infoMessage.set(this.i18n.t('verify.resent'));
      } else {
        this.errorMessage.set(res.error ?? this.i18n.t('verify.resendError'));
      }
    });
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
          this.router.navigate(['/discover']);
        } else {
          this.isLoading.set(false);
          this.errorMessage.set(this.i18n.t('login.googleError'));
        }
      });
    });
  }

  protected formatStat(val?: number | null): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toString();
  }
}
