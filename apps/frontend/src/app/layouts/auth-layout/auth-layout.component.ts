import { I18nService } from '../../core/services/i18n.service';
import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

/**
 * AuthLayoutComponent — Shell para rutas públicas (login).
 * Sin sidebar ni topbar. Centra el contenido en pantalla completa.
 */
@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterOutlet, TranslatePipe],
  templateUrl: './auth-layout.component.html',
  styleUrl: './auth-layout.component.css',
})
export class AuthLayoutComponent {
  readonly lang = inject(I18nService).lang;}
