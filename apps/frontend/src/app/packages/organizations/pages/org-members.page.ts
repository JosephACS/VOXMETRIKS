import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Membership } from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';
import { AuthService } from '../../../core/services/auth.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-org-members-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page org-page--members" data-testid="org-members-page">
      <header class="org-page__header org-page__header--split">
        <div>
          <span class="org-page__eyebrow">Equipo y acceso</span>
          <h1>{{ 'organizations.members.title' | t:lang() }}</h1>
          <p class="lede">{{ 'organizations.members.lede' | t:lang() }}</p>
        </div>
        <div class="org-actions org-members-head-actions">
          @if (ctx.hasPermission('member.invite')) {
            <a class="org-btn" [routerLink]="['/organizations', orgId, 'invitations']">Invitar persona</a>
          }
          @if (ctx.hasPermission('role.view')) {
            <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId, 'roles']">Roles y permisos</a>
          }
        </div>
      </header>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }

      <div class="org-members-summary" aria-label="Resumen del equipo">
        <article><span>Total</span><strong>{{ total }}</strong><small>personas registradas</small></article>
        <article><span>Activos</span><strong>{{ activeCount() }}</strong><small>con acceso al espacio</small></article>
        <article><span>Administración</span><strong>{{ adminCount() }}</strong><small>con permisos de gestión</small></article>
      </div>

      @if (loading()) {
        <div class="org-card org-loading-card"><span class="org-spinner"></span><p>{{ 'organizations.members.loading' | t:lang() }}</p></div>
      } @else if (!items().length) {
        <div class="org-card org-members-empty">
          <span aria-hidden="true">+</span>
          <strong>Tu equipo empieza aquí</strong>
          <p class="org-muted">{{ 'organizations.members.empty' | t:lang() }}</p>
          @if (ctx.hasPermission('member.invite')) {
            <a class="org-btn" [routerLink]="['/organizations', orgId, 'invitations']">Enviar invitación</a>
          }
        </div>
      } @else {
        <div class="org-card org-members-card">
          <div class="org-members-card__head">
            <div><span class="org-section-kicker">Personas</span><h2>Accesos del espacio</h2></div>
            <span class="org-role-count">{{ total }} {{ total === 1 ? 'miembro' : 'miembros' }}</span>
          </div>
          <ul class="org-member-list">
            @for (m of items(); track m.id) {
              <li class="org-member-row">
                <span class="org-avatar" aria-hidden="true">{{ memberInitials(m) }}</span>
                <div class="org-member-row__copy">
                  <div class="org-member-row__name">
                    <strong>{{ memberDisplayName(m) }}</strong>
                    @if (m.user_id === currentUserId) {
                      <span class="org-badge">{{ 'organizations.members.you' | t:lang() }}</span>
                    }
                  </div>
                  <div class="org-muted">{{ roleLabels(m) || 'Sin rol asignado' }} · {{ m.status_label || humanMemberStatus(m.status) }}</div>
                </div>
                <div class="org-actions">
                  @if (canSuspend() && m.status === 'active' && m.user_id !== currentUserId) {
                    <button type="button" class="org-btn org-btn--ghost" (click)="act(m, 'suspend')">
                      {{ 'organizations.members.suspend' | t:lang() }}
                    </button>
                  }
                  @if (canSuspend() && m.status === 'suspended') {
                    <button type="button" class="org-btn org-btn--ghost" (click)="act(m, 'reactivate')">
                      {{ 'organizations.members.reactivate' | t:lang() }}
                    </button>
                  }
                  @if (canRemove() && m.user_id !== currentUserId && m.status !== 'removed') {
                    <button type="button" class="org-btn org-btn--danger" (click)="remove(m)">
                      {{ 'organizations.members.remove' | t:lang() }}
                    </button>
                  }
                  @if (m.user_id === currentUserId && m.status === 'active') {
                    <button type="button" class="org-btn org-btn--ghost" (click)="act(m, 'leave')">
                      {{ 'organizations.members.leave' | t:lang() }}
                    </button>
                  }
                  @if (ctx.hasPermission('role.assign') && m.status === 'active') {
                    <a
                      class="org-btn org-btn--ghost"
                      [routerLink]="['/organizations', orgId, 'roles']"
                      [queryParams]="{ member: m.id }"
                      >{{ 'organizations.roles.manageMember' | t:lang() }}</a
                    >
                  }
                </div>
              </li>
            }
          </ul>
          @if (total > limit) {
            <div class="org-members-pager">
              <p class="org-muted">{{ 'common.page' | t:lang() }} {{ page }} · {{ 'common.total' | t:lang() }} {{ total }}</p>
              <div class="org-actions">
                <button type="button" class="org-btn org-btn--ghost" [disabled]="page <= 1" (click)="go(page - 1)">{{ 'common.prev' | t:lang() }}</button>
                <button type="button" class="org-btn org-btn--ghost" [disabled]="page * limit >= total" (click)="go(page + 1)">{{ 'common.next' | t:lang() }}</button>
              </div>
            </div>
          }
        </div>
      }
    </section>
  `,
})
export class OrgMembersPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  readonly ctx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);
  private readonly auth = inject(AuthService);

  orgId = 0;
  page = 1;
  limit = 50;
  total = 0;
  currentUserId = 0;

  readonly items = signal<Membership[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  canSuspend(): boolean {
    return this.ctx.hasPermission('member.suspend');
  }

  canRemove(): boolean {
    return this.ctx.hasPermission('member.remove');
  }

  humanMemberStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'active') return 'Activo';
    if (s === 'suspended') return 'Suspendido';
    if (s === 'removed') return 'Eliminado';
    if (s === 'left') return 'Salió';
    return status || 'Sin datos';
  }

  memberDisplayName(m: Membership): string {
    return m.user?.display_name?.trim() || 'Miembro';
  }

  roleLabels(m: Membership): string {
    return (m.roles || []).map((r) => this.humanRole(r.code || r.label)).join(', ');
  }

  memberInitials(m: Membership): string {
    return this.memberDisplayName(m).split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  }

  activeCount(): number {
    return this.items().filter((member) => member.status === 'active').length;
  }

  adminCount(): number {
    return this.items().filter((member) => (member.roles || []).some((role) => ['owner', 'organization_admin', 'org_admin', 'admin'].includes((role.code || '').toLowerCase()))).length;
  }

  private humanRole(code: string): string {
    const value = (code || '').toLowerCase();
    if (value === 'owner') return 'Propietario';
    if (['organization_admin', 'org_admin', 'admin', 'administrator'].includes(value)) return 'Administrador';
    if (value === 'billing_admin') return 'Facturación';
    if (value === 'sales_manager') return 'Gestión comercial';
    if (value === 'viewer') return 'Solo lectura';
    return code.replace(/_/g, ' ');
  }

  async ngOnInit(): Promise<void> {
    this.orgId = Number(this.route.snapshot.paramMap.get('id'));
    this.currentUserId = this.auth.getUser()?.id ?? 0;
    await this.load();
  }

  async go(p: number): Promise<void> {
    this.page = p;
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const res = await firstValueFrom(this.api.listMembers(this.orgId, this.page, this.limit));
      this.items.set(res.items);
      this.total = res.total;
      this.page = res.page;
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : this.i18n.t('organizations.members.loadFailed'));
      this.items.set([]);
    } finally {
      this.loading.set(false);
    }
  }

  async act(m: Membership, action: 'suspend' | 'reactivate' | 'leave'): Promise<void> {
    const label =
      action === 'leave'
        ? this.i18n.t('organizations.members.leaveConfirm')
        : action === 'suspend'
          ? this.i18n.t('organizations.members.suspendConfirm', { id: m.id })
          : this.i18n.t('organizations.members.reactivateConfirm', { id: m.id });
    if (!confirm(label)) return;
    this.error.set(null);
    try {
      await firstValueFrom(this.api.memberAction(this.orgId, m.id, action));
      if (action === 'leave') await this.ctx.bootstrap();
      await this.load();
    } catch (e) {
      this.error.set(
        e instanceof OrganizationsApiError
          ? e.status === 409
            ? this.i18n.t('organizations.members.businessRule', { message: e.message })
            : e.message
          : this.i18n.t('common.actionFailed'),
      );
    }
  }

  async remove(m: Membership): Promise<void> {
    if (!confirm(this.i18n.t('organizations.members.removeConfirm', { id: m.id }))) return;
    try {
      await firstValueFrom(this.api.removeMember(this.orgId, m.id));
      await this.load();
    } catch (e) {
      this.error.set(
        e instanceof OrganizationsApiError
          ? e.status === 409
            ? this.i18n.t('organizations.members.businessRule', { message: e.message })
            : e.message
          : this.i18n.t('organizations.members.removeFailed'),
      );
    }
  }
}
