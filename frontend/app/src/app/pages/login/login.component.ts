/**
 * LoginComponent
 * ==============
 * Página de inicio de sesión con:
 * - Formulario reactivo con validaciones
 * - Carga de stats reales del backend para el preview
 * - Latencia artificial para UX realista
 * - Diseño VOXMETRIK con fondo oscuro + resplandores verdes
 */

import { Component, inject, signal, OnInit } from '@angular/core';
import { Router }                             from '@angular/router';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
} from '@angular/forms';

import { AuthService }  from '../../core/services/auth.service';
import { StatsService } from '../../services/stats.service';
import { StatsSummary } from '../../shared/models/api.models';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl:    './login.component.css',
})
export class LoginComponent implements OnInit {
  private readonly auth   = inject(AuthService);
  private readonly router = inject(Router);
  private readonly fb     = inject(FormBuilder);
  private readonly stats  = inject(StatsService);

  protected readonly isLoading    = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly showPassword = signal(false);
  protected readonly summary      = signal<StatsSummary | null>(null);

  protected readonly form = this.fb.group({
    email:    ['admin@voxmetrik.io', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(4)]],
    remember: [false],
  });

  get emailCtrl()    { return this.form.controls['email'];    }
  get passwordCtrl() { return this.form.controls['password']; }

  ngOnInit(): void {
    // Carga datos reales del backend para mostrar en el preview de estadísticas
    this.stats.getSummary().subscribe({
      next: data => this.summary.set(data),
      error: ()   => { /* silencioso — el login funciona sin esto */ },
    });
  }

  protected togglePassword(): void {
    this.showPassword.update(v => !v);
  }

  protected onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    const { email, password } = this.form.getRawValue();

    // auth.login() devuelve Promise<boolean>
    this.auth.login(email!, password!).then(ok => {
      if (ok) {
        this.router.navigate(['/dashboard']);
      } else {
        this.errorMessage.set('Credenciales inválidas. Intenta de nuevo.');
        this.isLoading.set(false);
      }
    });
  }

  protected formatStat(val?: number | null): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000)     return `${(val / 1_000).toFixed(1)}K`;
    return val.toString();
  }
}
