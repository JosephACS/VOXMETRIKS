import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { BusinessRole, Permission } from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';

@Component({
  selector: 'app-org-roles-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-roles-page">
      <h1>Roles y permisos</h1>
      <p class="lede">
        Catálogo del sistema (solo lectura). No se editan roles técnicos user/admin/engineer aquí.
        No hay custom roles en 016.
      </p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }
      @if (ok()) {
        <div class="org-alert org-alert--ok" role="status">{{ ok() }}</div>
      }

      <div class="org-card">
        <h2>Roles del sistema</h2>
        @if (loading()) {
          <p class="org-muted">Cargando…</p>
        } @else {
          <ul>
            @for (r of roles(); track r.code) {
              <li><strong>{{ r.code }}</strong> — {{ r.display_name }}: {{ r.description }}</li>
            }
          </ul>
        }
      </div>

      <div class="org-card">
        <h2>Permisos</h2>
        <ul>
          @for (p of permissions(); track p.code) {
            <li><code>{{ p.code }}</code> — {{ p.description }}</li>
          }
        </ul>
      </div>

      @if (ctx.hasPermission('role.assign')) {
        <form class="org-card org-form" (ngSubmit)="applyRoles()">
          <h2>Asignar / revocar roles de un miembro</h2>
          <label>
            Member ID
            <input type="number" name="memberId" [(ngModel)]="memberId" required />
          </label>
          <label>
            Asignar (código)
            <select name="assign" [(ngModel)]="assignCode">
              <option value="">—</option>
              @for (r of roles(); track r.code) {
                <option [value]="r.code">{{ r.code }}</option>
              }
            </select>
          </label>
          <label>
            Revocar (código)
            <select name="revoke" [(ngModel)]="revokeCode">
              <option value="">—</option>
              @for (r of roles(); track r.code) {
                <option [value]="r.code">{{ r.code }}</option>
              }
            </select>
          </label>
          <p class="org-muted">Advertencia: no se puede dejar la organización sin último owner (409 del backend).</p>
          <button class="org-btn" type="submit" [disabled]="busy() || !memberId">Aplicar</button>
        </form>
      }

      <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId, 'members']">Volver a miembros</a>
    </section>
  `,
})
export class OrgRolesPageComponent implements OnInit {
  private readonly api = inject(OrganizationsApiService);
  readonly ctx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);

  orgId = 0;
  memberId: number | null = null;
  assignCode = '';
  revokeCode = '';

  readonly roles = signal<BusinessRole[]>([]);
  readonly permissions = signal<Permission[]>([]);
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly ok = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.orgId = Number(this.route.snapshot.paramMap.get('id'));
    const q = this.route.snapshot.queryParamMap.get('member');
    if (q) this.memberId = Number(q);
    this.loading.set(true);
    try {
      const [roles, perms] = await Promise.all([
        firstValueFrom(this.api.listRoles(this.orgId)),
        firstValueFrom(this.api.listPermissions(this.orgId)),
      ]);
      this.roles.set(roles);
      this.permissions.set(perms);
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'Error al cargar roles');
    } finally {
      this.loading.set(false);
    }
  }

  async applyRoles(): Promise<void> {
    if (!this.memberId || this.busy()) return;
    if (!confirm('¿Confirmar cambio de roles? Recuerda la regla del último owner.')) return;
    this.busy.set(true);
    this.error.set(null);
    this.ok.set(null);
    try {
      const assign = this.assignCode ? [this.assignCode] : [];
      const revoke = this.revokeCode ? [this.revokeCode] : [];
      const codes = await firstValueFrom(
        this.api.putMemberRoles(this.orgId, this.memberId, assign, revoke),
      );
      this.ok.set(`Roles activos del miembro: ${codes.join(', ') || '(ninguno)'}`);
      this.assignCode = '';
      this.revokeCode = '';
    } catch (e) {
      this.error.set(
        e instanceof OrganizationsApiError
          ? e.status === 409
            ? `Regla (409): ${e.message}`
            : e.message
          : 'No se pudieron actualizar roles',
      );
    } finally {
      this.busy.set(false);
    }
  }
}
