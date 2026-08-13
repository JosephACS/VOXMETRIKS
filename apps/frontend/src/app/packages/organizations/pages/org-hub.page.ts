import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { OrganizationContextService } from '../services/organization-context.service';
import { OrganizationsApiService } from '../services/organizations-api.service';
import { Membership, Organization } from '../models/organization.models';
import { BillingApiService } from '../../billing/services/billing-api.service';
import { SubscriptionsApiService } from '../../subscriptions/services/subscriptions-api.service';
import { Invoice } from '../../billing/models/billing.models';
import { Plan, Subscription } from '../../subscriptions/models/subscriptions.models';
import { AuthService } from '../../../core/services/auth.service';
import {
  productInvoiceNumber,
  productOrgSlugDisplay,
} from '../../../shared/utils/product-presentation.util';

@Component({
  selector: 'app-org-hub-page',
  standalone: true,
  imports: [CommonModule, RouterLink, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/workspace-settings.css'],
  template: `
    <div class="vx-enterprise ws-page" data-testid="org-workspace">
      <header class="ws-head">
        <p class="ws-kicker">Organización</p>
        <h1 class="ws-title">{{ orgName() }}</h1>
        <p class="ws-sub">Información, miembros y configuración del espacio de trabajo.</p>
      </header>

      @if (!orgId()) {
        <app-enterprise-org-required />
      } @else if (loading()) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <section class="ws-section" aria-label="Identidad">
          <h2 class="ws-section__title">Espacio de trabajo</h2>
          <div class="ws-identity">
            <p class="ws-identity__name">{{ orgName() }}</p>
            <div class="ws-meta">
              <span class="ws-pill">{{ orgStatusLabel() }}</span>
              @if (org()?.slug) {
                <span class="ws-pill ws-pill--muted">{{ orgSlugLabel() }}</span>
              }
              @if (planName()) {
                <span class="ws-pill ws-pill--muted">Plan {{ planName() }}</span>
              }
            </div>
            <dl class="ws-dl">
              @if (org()?.legal_name) {
                <div>
                  <dt>Nombre legal</dt>
                  <dd>{{ org()!.legal_name }}</dd>
                </div>
              }
              @if (org()?.default_currency) {
                <div>
                  <dt>Moneda</dt>
                  <dd>{{ org()!.default_currency }}</dd>
                </div>
              }
              @if (org()?.timezone) {
                <div>
                  <dt>Zona horaria</dt>
                  <dd>{{ org()!.timezone }}</dd>
                </div>
              }
              @if (org()?.country_code) {
                <div>
                  <dt>País</dt>
                  <dd>{{ org()!.country_code }}</dd>
                </div>
              }
              @if (myRolesLabel()) {
                <div>
                  <dt>Tu rol</dt>
                  <dd>{{ myRolesLabel() }}</dd>
                </div>
              }
            </dl>
          </div>
        </section>

        <section class="ws-section" aria-label="Plan">
          <h2 class="ws-section__title">Plan</h2>
          @if (!subscription()) {
            <p class="ws-empty">Sin datos de suscripción para esta organización.</p>
            <div class="ws-actions" style="margin-top: 0.75rem">
              <a class="primary" routerLink="/subscriptions/select-plan">Elegir plan</a>
              <a routerLink="/subscriptions/overview">Ver plan y facturación</a>
            </div>
          } @else {
            <dl class="ws-dl">
              <div>
                <dt>Plan</dt>
                <dd>{{ planName() || 'Sin datos' }}</dd>
              </div>
              <div>
                <dt>Estado</dt>
                <dd>{{ humanSubStatus(subscription()!.status) }}</dd>
              </div>
              @if (periodLabel()) {
                <div>
                  <dt>Periodo</dt>
                  <dd>{{ periodLabel() }}</dd>
                </div>
              }
              @if (renewalLabel()) {
                <div>
                  <dt>Renovación</dt>
                  <dd>{{ renewalLabel() }}</dd>
                </div>
              }
            </dl>
            <div class="ws-actions" style="margin-top: 0.85rem">
              <a class="primary" routerLink="/subscriptions/overview">Ver plan y facturación</a>
              <a routerLink="/subscriptions/plans">Cambiar plan</a>
              <a routerLink="/billing/invoices">Ver facturas</a>
            </div>
          }
        </section>

        <section class="ws-section" aria-label="Acciones">
          <h2 class="ws-section__title">Acciones</h2>
          <div class="ws-actions">
            <a class="primary" [routerLink]="['/organizations', orgId(), 'members']">Gestionar miembros</a>
            <a [routerLink]="['/organizations', orgId(), 'settings']">Actualizar configuración</a>
            @if (canInvite()) {
              <a [routerLink]="['/organizations', orgId(), 'invitations']">Invitaciones</a>
            }
            @if (canRoles()) {
              <a [routerLink]="['/organizations', orgId(), 'roles']">Roles</a>
            }
            <a routerLink="/billing/invoices">Revisar pagos</a>
          </div>
        </section>

        <section class="ws-section" aria-label="Miembros">
          <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:baseline;flex-wrap:wrap">
            <h2 class="ws-section__title" style="margin:0">Miembros</h2>
            <a class="ws-link" [routerLink]="['/organizations', orgId(), 'members']">Ver todos</a>
          </div>
          @if (!members().length) {
            <p class="ws-empty" style="margin-top:0.75rem">No hay miembros para mostrar.</p>
          } @else {
            <ul class="ws-rows">
              @for (m of members(); track m.id) {
                <li>
                  <div>
                    <p class="ws-row__title">
                      {{ memberLabel(m) }}
                      @if (m.user_id === currentUserId) {
                        <span class="ws-pill ws-pill--muted" style="margin-left:0.35rem">Tú</span>
                      }
                    </p>
                    <p class="ws-row__meta">Estado: {{ humanMemberStatus(m.status) }}</p>
                  </div>
                  <div class="ws-row__side">
                    <a class="ws-link" [routerLink]="['/organizations', orgId(), 'members']">Gestionar</a>
                  </div>
                </li>
              }
            </ul>
          }
        </section>

        <section class="ws-section" aria-label="Facturación">
          <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:baseline;flex-wrap:wrap">
            <h2 class="ws-section__title" style="margin:0">Facturación</h2>
            <a class="ws-link" routerLink="/billing/invoices">Ver facturas</a>
          </div>
          @if (!invoices().length) {
            <p class="ws-empty" style="margin-top:0.75rem">No hay facturas registradas.</p>
          } @else {
            <ul class="ws-rows">
              @for (inv of invoices(); track inv.id) {
                <li>
                  <div>
                    <p class="ws-row__title">{{ invoiceLabel(inv) }}</p>
                    <p class="ws-row__meta">
                      {{ invoiceDate(inv) }}
                      @if (inv.due_date) {
                        · Vence {{ formatDate(inv.due_date) }}
                      }
                    </p>
                  </div>
                  <div class="ws-row__side">
                    <span class="ws-invoice-amount">{{ formatMoney(inv.total, inv.currency) }}</span>
                    <span
                      class="ws-pill"
                      [class.ws-pill--warn]="invoiceTone(inv.status) === 'warn'"
                      [class.ws-pill--danger]="invoiceTone(inv.status) === 'danger'"
                      [class.ws-pill--muted]="invoiceTone(inv.status) === 'muted'"
                      >{{ humanInvoiceStatus(inv.status) }}</span
                    >
                    <a class="ws-link" [routerLink]="['/billing/invoices', inv.id]">Ver factura</a>
                  </div>
                </li>
              }
            </ul>
          }
        </section>

        <section class="ws-section" aria-label="Configuración">
          <h2 class="ws-section__title">Configuración</h2>
          <ul class="ws-rows">
            <li>
              <div>
                <p class="ws-row__title">Perfil de organización</p>
                <p class="ws-row__meta">Nombre, moneda y datos básicos</p>
              </div>
              <div class="ws-row__side">
                <a class="ws-link" [routerLink]="['/organizations', orgId(), 'settings']">Abrir</a>
              </div>
            </li>
            <li>
              <div>
                <p class="ws-row__title">Perfil de facturación</p>
                <p class="ws-row__meta">Datos fiscales y contacto de cobro</p>
              </div>
              <div class="ws-row__side">
                <a class="ws-link" routerLink="/billing/profile">Abrir</a>
              </div>
            </li>
            @if (canAudit()) {
              <li>
                <div>
                  <p class="ws-row__title">Auditoría</p>
                  <p class="ws-row__meta">Historial de cambios del espacio</p>
                </div>
                <div class="ws-row__side">
                  <a class="ws-link" [routerLink]="['/organizations', orgId(), 'audit']">Abrir</a>
                </div>
              </li>
            }
          </ul>
        </section>
      }
    </div>
  `,
})
export class OrgHubPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly api = inject(OrganizationsApiService);
  private readonly billing = inject(BillingApiService);
  private readonly subs = inject(SubscriptionsApiService);
  private readonly auth = inject(AuthService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly org = signal<Organization | null>(null);
  readonly members = signal<Membership[]>([]);
  readonly invoices = signal<Invoice[]>([]);
  readonly subscription = signal<Subscription | null>(null);
  readonly planName = signal<string | null>(null);

  readonly orgId = computed(() => {
    const fromRoute = Number(this.route.snapshot.paramMap.get('id'));
    if (Number.isFinite(fromRoute) && fromRoute > 0) return fromRoute;
    return this.orgCtx.activeOrganization()?.id ?? null;
  });

  readonly orgName = computed(
    () => this.org()?.display_name || this.orgCtx.activeOrganization()?.display_name || 'Organización',
  );

  orgSlugLabel(): string {
    return productOrgSlugDisplay(this.org()?.slug);
  }

  invoiceLabel(inv: Invoice): string {
    return productInvoiceNumber(inv.invoice_number, inv.id);
  }

  currentUserId = 0;

  ngOnInit(): void {
    this.currentUserId = this.auth.getUser()?.id ?? 0;
    this.load();
  }

  canInvite(): boolean {
    return this.orgCtx.hasPermission('member.invite');
  }

  canRoles(): boolean {
    return this.orgCtx.hasPermission('role.view');
  }

  canAudit(): boolean {
    return this.orgCtx.hasPermission('audit.view');
  }

  orgStatusLabel(): string {
    const s = this.org()?.status || this.orgCtx.activeOrganization()?.status || '';
    return this.humanOrgStatus(s);
  }

  myRolesLabel(): string | null {
    const list = this.orgCtx.roles() || [];
    if (!list.length) return null;
    const human = [...new Set(list.map((r) => this.humanRole(r)))];
    return human.join(', ');
  }

  memberLabel(m: Membership): string {
    return `Usuario ${m.user_id}`;
  }

  humanMemberStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'active') return 'Activo';
    if (s === 'suspended') return 'Suspendido';
    if (s === 'removed') return 'Eliminado';
    if (s === 'left') return 'Salió';
    return status || 'Sin datos';
  }

  humanOrgStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'active') return 'Activa';
    if (s === 'suspended' || s === 'suspended_by_platform') return 'Suspendida';
    if (s === 'closed') return 'Cerrada';
    if (s === 'provisioning') return 'En provisión';
    return status || 'Sin datos';
  }

  humanRole(code: string): string {
    const c = (code || '').toLowerCase();
    if (c === 'organization_admin' || c === 'org_admin' || c === 'owner' || c === 'admin' || c === 'administrator') {
      return 'Administrador';
    }
    if (c === 'platform_admin') return 'Administración de plataforma';
    if (c === 'data_ops' || c === 'engineer' || c === 'data_engineer') return 'Ingeniería de datos';
    if (c === 'member' || c === 'org_member') return 'Miembro';
    if (c === 'billing_admin') return 'Facturación';
    return code.replace(/_/g, ' ');
  }

  humanSubStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'active') return 'Activa';
    if (s === 'trialing') return 'En prueba';
    if (s === 'past_due') return 'Vencida';
    if (s === 'canceled' || s === 'cancelled') return 'Cancelada';
    if (s === 'expired') return 'Expirada';
    return status || 'Sin datos';
  }

  humanInvoiceStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'paid') return 'Pagada';
    if (s === 'past_due') return 'Vencida';
    if (s === 'failed') return 'Fallida';
    if (s === 'issued' || s === 'draft' || s === 'partially_paid' || s === 'pending') return 'Pendiente';
    if (s === 'void') return 'Anulada';
    return status || 'Sin datos';
  }

  invoiceTone(status: string): 'ok' | 'warn' | 'danger' | 'muted' {
    const s = (status || '').toLowerCase();
    if (s === 'paid') return 'ok';
    if (s === 'past_due' || s === 'failed') return 'danger';
    if (s === 'issued' || s === 'partially_paid' || s === 'pending') return 'warn';
    return 'muted';
  }

  periodLabel(): string | null {
    const sub = this.subscription();
    if (!sub?.current_period_start || !sub?.current_period_end) return null;
    return `${this.formatDate(sub.current_period_start)} – ${this.formatDate(sub.current_period_end)}`;
  }

  renewalLabel(): string | null {
    const sub = this.subscription();
    if (!sub?.current_period_end) return null;
    if (sub.cancel_at_period_end) return `Cancela el ${this.formatDate(sub.current_period_end)}`;
    return this.formatDate(sub.current_period_end);
  }

  invoiceDate(inv: Invoice): string {
    const raw = inv.issued_at || inv.created_at;
    return raw ? this.formatDate(raw) : 'Sin fecha';
  }

  formatDate(iso: string): string {
    const d = Date.parse(iso);
    if (Number.isNaN(d)) return iso.slice(0, 10);
    return new Date(d)
      .toLocaleDateString('es-ES', { year: 'numeric', month: 'short', day: 'numeric' })
      .replace(/\./g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  formatMoney(amount: number, currency: string): string {
    try {
      return amount.toLocaleString('es-ES', {
        style: 'currency',
        currency: currency || 'USD',
        maximumFractionDigits: 2,
      });
    } catch {
      return `${amount} ${currency || ''}`.trim();
    }
  }

  load(): void {
    const id = this.orgId();
    if (!id) {
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.error.set(null);

    const fromCtx = this.orgCtx.activeOrganization();
    if (fromCtx && fromCtx.id === id) this.org.set(fromCtx);

    forkJoin({
      org: this.api.get(id).pipe(catchError(() => of(fromCtx))),
      members: this.api.listMembers(id, 1, 8).pipe(catchError(() => of({ items: [], page: 1, limit: 8, total: 0 }))),
      invoices: this.billing.listInvoices(id, { page: 1, page_size: 6 }).pipe(catchError(() => of({ items: [] as Invoice[] }))),
      subscriptions: this.subs.listSubscriptions(id, { page: 1, limit: 10 }).pipe(
        catchError(() => of({ items: [] as Subscription[] })),
      ),
      plans: this.subs.listPlans({ page: 1, limit: 50 }).pipe(catchError(() => of({ items: [] as Plan[] }))),
    }).subscribe({
      next: (res) => {
        const org = res.org || fromCtx || null;
        this.org.set(org);
        this.members.set(res.members.items || []);

        const invItems = res.invoices.items ?? [];
        this.invoices.set(invItems.slice(0, 6));

        const subs = res.subscriptions.items || [];
        const active =
          subs.find((s) => ['active', 'trialing', 'past_due'].includes(s.status)) || subs[0] || null;
        this.subscription.set(active);
        if (active) {
          const plan = (res.plans.items || []).find((p) => p.id === active.plan_id);
          this.planName.set(plan?.display_name || null);
        } else {
          this.planName.set(null);
        }
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el espacio de trabajo.');
        this.loading.set(false);
      },
    });
  }
}
