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
    <section class="org-page" data-testid="org-members-page">
      <h1>{{ 'organizations.members.title' | t:lang() }}</h1>
      <p class="lede">{{ 'organizations.members.lede' | t:lang() }}</p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }

      <div class="org-actions" style="margin-bottom: 1rem">
        @if (ctx.hasPermission('member.invite')) {
          <a class="org-btn" [routerLink]="['/organizations', orgId, 'invitations']">{{
            'organizations.invitations.title' | t:lang()
          }}</a>
        }
        @if (ctx.hasPermission('role.view')) {
          <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId, 'roles']">{{
            'organizations.roles.title' | t:lang()
          }}</a>
        }
      </div>

      @if (loading()) {
        <p class="org-muted">{{ 'organizations.members.loading' | t:lang() }}</p>
      } @else if (!items().length) {
        <div class="org-card">
          <p class="org-muted">{{ 'organizations.members.empty' | t:lang() }}</p>
        </div>
      } @else {
        <div class="org-card" style="overflow-x: auto">
          <table class="org-table">
            <thead>
              <tr>
                <th>{{ 'common.id' | t:lang() }}</th>
                <th>{{ 'organizations.members.col.user' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th>{{ 'common.actions' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (m of items(); track m.id) {
                <tr>
                  <td>{{ m.id }}</td>
                  <td>
                    #{{ m.user_id }}
                    @if (m.user_id === currentUserId) {
                      <span class="org-badge">{{ 'organizations.members.you' | t:lang() }}</span>
                    }
                  </td>
                  <td><span class="org-badge">{{ m.status }}</span></td>
                  <td>
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
                          >{{ 'organizations.roles.title' | t:lang() }}</a
                        >
                      }
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
          <p class="org-muted">
            {{ 'common.page' | t:lang() }} {{ page }} · {{ 'common.total' | t:lang() }} {{ total }}
          </p>
          <div class="org-actions">
            <button
              type="button"
              class="org-btn org-btn--ghost"
              [disabled]="page <= 1"
              (click)="go(page - 1)"
            >
              {{ 'common.prev' | t:lang() }}
            </button>
            <button
              type="button"
              class="org-btn org-btn--ghost"
              [disabled]="page * limit >= total"
              (click)="go(page + 1)"
            >
              {{ 'common.next' | t:lang() }}
            </button>
          </div>
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
