import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { BusinessRole, Membership, Permission } from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-org-roles-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page org-page--roles" data-testid="org-roles-page">
      <header class="org-page__header org-page__header--split">
        <div>
          <span class="org-page__eyebrow">{{ 'organizations.roles.eyebrow' | t:lang() }}</span>
          <h1>{{ 'organizations.roles.title' | t:lang() }}</h1>
          <p class="lede">{{ 'organizations.roles.lede' | t:lang() }}</p>
        </div>
        <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId, 'members']">
          ← {{ 'organizations.roles.back' | t:lang() }}
        </a>
      </header>

      @if (ctx.roles().includes('owner')) {
        <div class="org-owner-banner">
          <span class="org-owner-banner__icon" aria-hidden="true">✓</span>
          <div><strong>{{ 'organizations.roles.ownerTitle' | t:lang() }}</strong><span>{{ 'organizations.roles.ownerText' | t:lang() }}</span></div>
        </div>
      }

      @if (error()) { <div class="org-alert org-alert--error" role="alert">{{ error() }}</div> }
      @if (ok()) { <div class="org-alert org-alert--ok" role="status">{{ ok() }}</div> }

      @if (loading()) {
        <div class="org-card org-loading-card"><span class="org-spinner"></span><p>{{ 'common.loading' | t:lang() }}</p></div>
      } @else {
        <div class="org-role-layout">
          <aside class="org-card org-member-picker">
            <span class="org-section-kicker">{{ 'organizations.roles.memberStep' | t:lang() }}</span>
            <h2>{{ 'organizations.roles.chooseMember' | t:lang() }}</h2>
            <p class="org-muted">{{ 'organizations.roles.chooseMemberHint' | t:lang() }}</p>
            <label>
              {{ 'organizations.roles.memberLabel' | t:lang() }}
              <select name="memberId" [(ngModel)]="memberId" (ngModelChange)="onMemberSelected()">
                <option [ngValue]="null">{{ 'organizations.roles.memberPlaceholder' | t:lang() }}</option>
                @for (member of members(); track member.id) {
                  <option [ngValue]="member.id">{{ memberName(member) }} · {{ roleSummary(member) }}</option>
                }
              </select>
            </label>

            @if (selectedMember(); as member) {
              <div class="org-selected-member">
                <span class="org-avatar" aria-hidden="true">{{ memberInitials(member) }}</span>
                <div><strong>{{ memberName(member) }}</strong><small>{{ member.user?.email || ('organizations.roles.noEmail' | t:lang()) }}</small></div>
              </div>
              <div class="org-current-access">
                <span>{{ 'organizations.roles.currentAccess' | t:lang() }}</span>
                <div>
                  @for (role of member.roles || []; track role.code) { <span class="org-badge org-badge--active">{{ memberRoleLabel(role.code, role.label) }}</span> }
                  @if (!(member.roles || []).length) { <span class="org-muted">{{ 'organizations.roles.noRoles' | t:lang() }}</span> }
                </div>
              </div>
            } @else {
              <div class="org-member-picker__empty"><span aria-hidden="true">↗</span>{{ 'organizations.roles.selectHelp' | t:lang() }}</div>
            }
          </aside>

          <main class="org-card org-access-editor" [class.is-disabled]="!selectedMember()">
            <div class="org-access-editor__header">
              <div>
                <span class="org-section-kicker">{{ 'organizations.roles.accessStep' | t:lang() }}</span>
                <h2>{{ 'organizations.roles.assignTitle' | t:lang() }}</h2>
                <p class="org-muted">{{ 'organizations.roles.assignHint' | t:lang() }}</p>
              </div>
              <span class="org-role-count">{{ selectedRoleCodes().length }} {{ 'organizations.roles.selected' | t:lang() }}</span>
            </div>

            <div class="org-role-grid">
              @for (role of roles(); track role.code) {
                <label class="org-role-option" [class.is-selected]="roleSelected(role.code)">
                  <input type="checkbox" [checked]="roleSelected(role.code)" [disabled]="!selectedMember() || busy()" (change)="toggleRole(role.code, $any($event.target).checked)" />
                  <span class="org-role-option__check" aria-hidden="true">✓</span>
                  <span class="org-role-option__copy"><strong>{{ roleName(role) }}</strong><small>{{ roleDescription(role) }}</small></span>
                  @if (role.code === 'owner') { <span class="org-role-option__owner">{{ 'organizations.roles.maximum' | t:lang() }}</span> }
                </label>
              }
            </div>

            <details class="org-permission-details">
              <summary>{{ 'organizations.roles.permissionDetails' | t:lang() }} · {{ permissions().length }}</summary>
              <div class="org-permission-groups">
                @for (group of permissionGroups(); track group.domain) {
                  <div><strong>{{ group.domain }}</strong><span>{{ group.count }} {{ 'organizations.roles.permissions' | t:lang() }}</span></div>
                }
              </div>
            </details>

            <div class="org-last-owner-note"><span aria-hidden="true">i</span>{{ 'organizations.roles.lastOwner' | t:lang() }}</div>
            @if (ctx.hasPermission('role.assign')) {
              <div class="org-actions org-actions--end">
                <button class="org-btn" type="button" [disabled]="busy() || !selectedMember() || !hasChanges()" (click)="applyRoles()">
                  {{ busy() ? ('organizations.roles.saving' | t:lang()) : ('organizations.roles.save' | t:lang()) }}
                </button>
              </div>
            }
          </main>
        </div>
      }
    </section>
  `,
})
export class OrgRolesPageComponent implements OnInit {
  private readonly i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private readonly api = inject(OrganizationsApiService);
  readonly ctx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);

  orgId = 0;
  memberId: number | null = null;

  readonly roles = signal<BusinessRole[]>([]);
  readonly permissions = signal<Permission[]>([]);
  readonly members = signal<Membership[]>([]);
  readonly selectedRoleCodes = signal<string[]>([]);
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly ok = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.orgId = Number(this.route.snapshot.paramMap.get('id'));
    const requestedMember = Number(this.route.snapshot.queryParamMap.get('member'));
    this.loading.set(true);
    try {
      const [roles, permissions, memberPage] = await Promise.all([
        firstValueFrom(this.api.listRoles(this.orgId)),
        firstValueFrom(this.api.listPermissions(this.orgId)),
        firstValueFrom(this.api.listMembers(this.orgId, 1, 100)),
      ]);
      this.roles.set(roles.filter((role) => role.is_active));
      this.permissions.set(permissions.filter((permission) => permission.is_active));
      this.members.set(memberPage.items.filter((member) => member.status === 'active'));
      if (requestedMember && this.members().some((member) => member.id === requestedMember)) this.memberId = requestedMember;
      else if (this.members().length === 1) this.memberId = this.members()[0].id;
      this.onMemberSelected();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : this.i18n.t('organizations.roles.loadError'));
    } finally {
      this.loading.set(false);
    }
  }

  selectedMember(): Membership | null {
    return this.members().find((member) => member.id === this.memberId) || null;
  }

  onMemberSelected(): void {
    this.ok.set(null);
    this.error.set(null);
    this.selectedRoleCodes.set((this.selectedMember()?.roles || []).map((role) => role.code));
  }

  toggleRole(code: string, checked: boolean): void {
    this.selectedRoleCodes.update((current) => checked ? Array.from(new Set([...current, code])) : current.filter((item) => item !== code));
  }

  roleSelected(code: string): boolean {
    return this.selectedRoleCodes().includes(code);
  }

  hasChanges(): boolean {
    const before = (this.selectedMember()?.roles || []).map((role) => role.code).sort().join('|');
    return before !== [...this.selectedRoleCodes()].sort().join('|');
  }

  memberName(member: Membership): string {
    return member.user?.display_name?.trim() || member.user?.email?.trim() || this.i18n.t('organizations.roles.memberFallback');
  }

  memberInitials(member: Membership): string {
    return this.memberName(member).split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  }

  roleSummary(member: Membership): string {
    return (member.roles || []).map((role) => this.memberRoleLabel(role.code, role.label)).join(', ') || this.i18n.t('organizations.roles.noRoles');
  }

  memberRoleLabel(code: string, fallback: string): string {
    const labels: Record<string, string> = {
      owner: 'Propietario',
      organization_admin: 'Administrador',
      org_admin: 'Administrador',
      billing_admin: 'Responsable de pagos',
      sales_manager: 'Gestión comercial',
      viewer: 'Solo lectura',
    };
    return labels[(code || '').toLowerCase()] || fallback || code.replace(/_/g, ' ');
  }

  roleName(role: BusinessRole): string {
    return this.i18n.t(`organizations.roles.role.${role.code}`);
  }

  roleDescription(role: BusinessRole): string {
    return this.i18n.t(`organizations.roles.description.${role.code}`);
  }

  permissionGroups(): { domain: string; count: number }[] {
    const groups = new Map<string, number>();
    for (const permission of this.permissions()) groups.set(permission.domain, (groups.get(permission.domain) || 0) + 1);
    return Array.from(groups, ([domain, count]) => ({ domain, count })).sort((a, b) => a.domain.localeCompare(b.domain));
  }

  async applyRoles(): Promise<void> {
    const member = this.selectedMember();
    if (!member || this.busy() || !this.hasChanges()) return;
    const current = new Set((member.roles || []).map((role) => role.code));
    const desired = new Set(this.selectedRoleCodes());
    const assign = [...desired].filter((code) => !current.has(code));
    const revoke = [...current].filter((code) => !desired.has(code));
    this.busy.set(true);
    this.error.set(null);
    this.ok.set(null);
    try {
      const activeCodes = await firstValueFrom(this.api.putMemberRoles(this.orgId, member.id, assign, revoke));
      const roleMap = new Map(this.roles().map((role) => [role.code, role]));
      this.members.update((items) => items.map((item) => item.id === member.id
        ? { ...item, roles: activeCodes.map((code) => ({ code, label: this.roleName(roleMap.get(code) || ({ code } as BusinessRole)) })) }
        : item));
      this.selectedRoleCodes.set(activeCodes);
      this.ok.set(this.i18n.t('organizations.roles.saved', { name: this.memberName(member) }));
      await this.ctx.bootstrap();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError
        ? e.status === 409 ? this.i18n.t('organizations.roles.lastOwner') : e.message
        : this.i18n.t('organizations.roles.updateError'));
    } finally {
      this.busy.set(false);
    }
  }
}
