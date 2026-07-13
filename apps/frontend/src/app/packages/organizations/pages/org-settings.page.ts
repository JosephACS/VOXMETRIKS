import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Organization } from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-org-settings-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-settings-page">
      <h1>{{ 'organizations.settings.title' | t:lang() }}</h1>
      <p class="lede">Consulta y actualiza campos autorizados. El slug no es editable.</p>

      @if (loading()) {
        <p class="org-muted">{{ 'common.loading' | t:lang() }}</p>
      }
      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }
      @if (ok()) {
        <div class="org-alert org-alert--ok" role="status">Cambios guardados.</div>
      }

      @if (org(); as o) {
        <form class="org-card org-form" (ngSubmit)="save()">
          <p>
            Estado:
            <span class="org-badge" [class.org-badge--active]="o.status === 'active'"
              [class.org-badge--closed]="o.status === 'closed'"
              [class.org-badge--suspended]="o.status === 'suspended_by_platform'">{{ o.status }}</span>
          </p>
          <label>
            Slug (no editable)
            <input [value]="o.slug" disabled />
          </label>
          <label>
            Nombre visible
            <input name="display_name" [(ngModel)]="displayName" [disabled]="!canUpdate() || saving()" />
          </label>
          <label>
            Nombre legal
            <input name="legal_name" [(ngModel)]="legalName" [disabled]="!canUpdate() || saving()" />
          </label>
          <label>
            Tipo
            <input name="organization_type" [(ngModel)]="organizationType" [disabled]="!canUpdate() || saving()" />
          </label>
          <label>
            País
            <input name="country_code" [(ngModel)]="countryCode" [disabled]="!canUpdate() || saving()" />
          </label>
          <label>
            Zona horaria
            <input name="timezone" [(ngModel)]="timezone" [disabled]="!canUpdate() || saving()" />
          </label>
          <label>
            Moneda
            <input name="default_currency" [(ngModel)]="defaultCurrency" [disabled]="!canUpdate() || saving()" />
          </label>
          <div class="org-actions">
            @if (canUpdate()) {
              <button class="org-btn" type="submit" [disabled]="saving()">{{ saving() ? 'Guardando…' : 'Guardar' }}</button>
            }
            <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', o.id, 'members']">{{ 'organizations.members.title' | t:lang() }}</a>
          </div>
        </form>

        @if (canClose() && o.status === 'active') {
          <div class="org-card">
            <h2>{{ 'organizations.settings.closeOrg' | t:lang() }}</h2>
            <p class="org-muted">Acción irreversible a nivel lógico. Requiere confirmación explícita.</p>
            <label>
              Escribe CLOSE para confirmar
              <input [(ngModel)]="closeConfirm" name="close_confirm" />
            </label>
            <label>
              Motivo (opcional)
              <input [(ngModel)]="closeReason" name="close_reason" />
            </label>
            <button
              type="button"
              class="org-btn org-btn--danger"
              [disabled]="closeConfirm !== 'CLOSE' || closing()"
              (click)="closeOrg()"
            >
              {{ 'organizations.settings.closeOrg' | t:lang() }}
            </button>
          </div>
        }
      }
    </section>
  `,
})
export class OrgSettingsPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  private readonly ctx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly org = signal<Organization | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly closing = signal(false);
  readonly error = signal<string | null>(null);
  readonly ok = signal(false);

  displayName = '';
  legalName = '';
  organizationType = '';
  countryCode = '';
  timezone = '';
  defaultCurrency = '';
  closeConfirm = '';
  closeReason = '';

  canUpdate(): boolean {
    return this.ctx.hasPermission('organization.update');
  }

  canClose(): boolean {
    return this.ctx.hasPermission('organization.close');
  }

  async ngOnInit(): Promise<void> {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loading.set(true);
    this.error.set(null);
    try {
      if (this.ctx.status() === 'idle') await this.ctx.bootstrap();
      const o = await firstValueFrom(this.api.get(id));
      this.org.set(o);
      this.displayName = o.display_name;
      this.legalName = o.legal_name ?? '';
      this.organizationType = o.organization_type;
      this.countryCode = o.country_code ?? '';
      this.timezone = o.timezone;
      this.defaultCurrency = o.default_currency;
      if (o.status === 'closed') {
        await this.router.navigate(['/organizations/closed']);
      } else if (o.status === 'suspended_by_platform') {
        await this.router.navigate(['/organizations/suspended']);
      }
    } catch (e) {
      this.mapError(e);
    } finally {
      this.loading.set(false);
    }
  }

  private mapError(e: unknown): void {
    if (e instanceof OrganizationsApiError) {
      if (e.status === 403) this.error.set('403: sin permiso para ver o editar esta organización.');
      else if (e.status === 404) this.error.set('404: organización no encontrada.');
      else this.error.set(e.message);
    } else {
      this.error.set('Error de red al cargar la organización.');
    }
  }

  async save(): Promise<void> {
    const o = this.org();
    if (!o || !this.canUpdate() || this.saving()) return;
    this.saving.set(true);
    this.error.set(null);
    this.ok.set(false);
    try {
      const updated = await firstValueFrom(
        this.api.update(o.id, {
          display_name: this.displayName.trim(),
          legal_name: this.legalName.trim() || undefined,
          organization_type: this.organizationType.trim() || undefined,
          country_code: this.countryCode.trim() || undefined,
          timezone: this.timezone.trim() || undefined,
          default_currency: this.defaultCurrency.trim() || undefined,
        }),
      );
      this.org.set(updated);
      this.ok.set(true);
      await this.ctx.bootstrap();
    } catch (e) {
      this.mapError(e);
    } finally {
      this.saving.set(false);
    }
  }

  async closeOrg(): Promise<void> {
    const o = this.org();
    if (!o || this.closeConfirm !== 'CLOSE' || !this.canClose()) return;
    this.closing.set(true);
    try {
      await firstValueFrom(this.api.close(o.id, this.closeReason.trim() || undefined));
      await this.ctx.bootstrap();
      await this.router.navigate(['/organizations/closed']);
    } catch (e) {
      this.mapError(e);
    } finally {
      this.closing.set(false);
    }
  }
}
