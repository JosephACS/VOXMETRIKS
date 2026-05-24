/**
 * LoginComponent — VOXMETRIK auth (login + register)
 */

import { Component, inject, signal, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
} from '@angular/forms';

import { AuthService } from '../../core/services/auth.service';
import { StatsService } from '../../packages/analytics/services/stats.service';
import { StatsSummary } from '../../shared/models/api.models';

type AuthMode = 'login' | 'register';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly stats = inject(StatsService);

  protected readonly mode = signal<AuthMode>('login');
  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly showPassword = signal(false);
  protected readonly summary = signal<StatsSummary | null>(null);

  protected readonly loginForm = this.fb.group({
    email: ['demo@voxmetrik.io', [Validators.required, Validators.email]],
    password: ['demo123', [Validators.required, Validators.minLength(4)]],
    remember: [true],
  });

  protected readonly registerForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(4)]],
    favoriteGenre: ['Pop'],
  });

  ngOnInit(): void {
    this.stats.getSummary().subscribe({
      next: (data) => this.summary.set(data),
      error: () => {},
    });
  }

  protected setMode(m: AuthMode): void {
    this.mode.set(m);
    this.errorMessage.set('');
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
    const { email, password, remember } = this.loginForm.getRawValue();
    this.auth.login(email!, password!, remember ?? true).then((ok) => {
      if (ok) {
        this.router.navigate(['/dashboard']);
      } else {
        this.errorMessage.set('Credenciales inválidas. Prueba demo@voxmetrik.io / demo123');
        this.isLoading.set(false);
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
      if (res.ok) {
        this.router.navigate(['/dashboard']);
      } else {
        this.errorMessage.set(res.error ?? 'Error al registrar');
        this.isLoading.set(false);
      }
    });
  }

  protected formatStat(val?: number | null): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toString();
  }
}
