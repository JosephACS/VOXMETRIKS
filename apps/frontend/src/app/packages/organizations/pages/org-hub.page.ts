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
import { SpaceContextService } from '../../../core/spaces/space-context.service';
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
      @if (!orgId()) {
        <app-enterprise-org-required />
      } @else if (loading()) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <header class="ws-hero">
          <span class="ws-hero__glow ws-hero__glow--one" aria-hidden="true"></span>
          <span class="ws-hero__glow ws-hero__glow--two" aria-hidden="true"></span>
          <div class="ws-hero__content">
            <div class="ws-meta">
              <span class="ws-pill">{{ orgStatusLabel() }}</span>
              @if (planName()) {
                <span class="ws-pill ws-pill--glass">Plan {{ planName() }}</span>
              }
            </div>
            <p class="ws-kicker">Centro empresarial</p>
            <h1 class="ws-title">{{ orgName() }}</h1>
            <p class="ws-sub">
              Controla el equipo, los clientes, los reportes y la facturación desde un solo lugar.
            </p>
            <div class="ws-actions ws-hero__actions">
              <a class="primary" routerLink="/business-analytics">Abrir panel</a>
              <a routerLink="/reports">Ver reportes</a>
              @if (canManageMembers()) {
                <a [routerLink]="['/organizations', orgId(), 'members']">Gestionar equipo</a>
              }
            </div>
          </div>
        </header>

        <section class="ws-kpis" aria-label="Resumen de la organización">
          <article class="ws-kpi">
            <span class="ws-kpi__icon" aria-hidden="true">E</span>
            <div>
              <p class="ws-kpi__label">Equipo</p>
              <p class="ws-kpi__value">{{ memberTotal() }}</p>
              <p class="ws-kpi__hint">{{ memberTotal() === 1 ? 'miembro activo' : 'miembros registrados' }}</p>
            </div>
          </article>
          <article class="ws-kpi">
            <span class="ws-kpi__icon" aria-hidden="true">P</span>
            <div>
              <p class="ws-kpi__label">Plan actual</p>
              <p class="ws-kpi__value ws-kpi__value--text">{{ planName() || 'Sin plan' }}</p>
              <p class="ws-kpi__hint">{{ subscription() ? humanSubStatus(subscription()!.status) : 'Requiere configuración' }}</p>
            </div>
          </article>
          <article class="ws-kpi">
            <span class="ws-kpi__icon" aria-hidden="true">F</span>
            <div>
              <p class="ws-kpi__label">Facturación</p>
              <p class="ws-kpi__value">{{ invoiceTotal() }}</p>
              <p class="ws-kpi__hint">{{ pendingInvoiceCount() ? pendingInvoiceCount() + ' por revisar' : 'sin pendientes recientes' }}</p>
            </div>
          </article>
          <article class="ws-kpi">
            <span class="ws-kpi__icon" aria-hidden="true">R</span>
            <div>
              <p class="ws-kpi__label">Tu acceso</p>
              <p class="ws-kpi__value ws-kpi__value--text">{{ myRolesLabel() || 'Miembro' }}</p>
              <p class="ws-kpi__hint">Permisos del espacio</p>
            </div>
          </article>
        </section>

        <div class="ws-dashboard-grid">
          <section class="ws-section ws-section--operations" aria-label="Operación empresarial">
            <div class="ws-section-head">
              <div>
                <p class="ws-section__eyebrow">Accesos principales</p>
                <h2 class="ws-section__heading">Tu operación</h2>
              </div>
              <span class="ws-section__badge">Todo conectado</span>
            </div>
            <div class="ws-module-grid">
              <a class="ws-module ws-module--accent" routerLink="/business-analytics">
                <span class="ws-module__mark" aria-hidden="true">01</span>
                <strong>Panel de negocio</strong>
                <span>Objetivos, alertas e indicadores clave.</span>
                <em>Abrir panel →</em>
              </a>
              <a class="ws-module" routerLink="/reports">
                <span class="ws-module__mark" aria-hidden="true">02</span>
                <strong>Informes</strong>
                <span>Reportes simples y análisis avanzados.</span>
                <em>Ver informes →</em>
              </a>
              <a class="ws-module" routerLink="/customer-success">
                <span class="ws-module__mark" aria-hidden="true">03</span>
                <strong>Clientes</strong>
                <span>Seguimiento, soporte y relaciones.</span>
                <em>Gestionar clientes →</em>
              </a>
              <a class="ws-module" routerLink="/campaigns">
                <span class="ws-module__mark" aria-hidden="true">04</span>
                <strong>Campañas</strong>
                <span>Acciones, resultados y rendimiento.</span>
                <em>Ver campañas →</em>
              </a>
            </div>
          </section>

          <aside class="ws-section ws-section--status" aria-label="Estado del espacio">
            <p class="ws-section__eyebrow">Estado del espacio</p>
            <h2 class="ws-section__heading">Todo bajo control</h2>
            <ul class="ws-checklist">
              <li><span></span><div><strong>Organización activa</strong><small>{{ orgSlugLabel() }}</small></div></li>
              <li><span></span><div><strong>Plan {{ planName() || 'pendiente' }}</strong><small>{{ subscription() ? humanSubStatus(subscription()!.status) : 'Configura un plan' }}</small></div></li>
              <li [class.is-pending]="!canManageMembers()"><span></span><div><strong>Acceso de equipo</strong><small>{{ canManageMembers() ? 'Listo para administrar' : 'Completa el plan' }}</small></div></li>
            </ul>
            @if (!canManageMembers()) {
              <a
                class="ws-status-cta"
                routerLink="/organizations/onboarding"
                [queryParams]="{ organization_id: orgId(), reason: 'plan' }"
                >Completar configuración</a
              >
            } @else {
              <a class="ws-status-cta" [routerLink]="['/organizations', orgId(), 'settings']">Configurar espacio</a>
            }
          </aside>
        </div>

        <div class="ws-split-grid">
          <section class="ws-section" aria-label="Miembros">
            <div class="ws-section-head ws-section-head--compact">
              <div>
                <p class="ws-section__eyebrow">Personas y permisos</p>
                <h2 class="ws-section__heading">Equipo</h2>
              </div>
              @if (canManageMembers()) {
                <a class="ws-link" [routerLink]="['/organizations', orgId(), 'members']">Ver todo</a>
              }
            </div>
            @if (!members().length) {
              <div class="ws-empty-state">
                <strong>Aún no hay miembros</strong>
                <span>Invita a tu equipo cuando estés listo.</span>
              </div>
            } @else {
              <ul class="ws-rows">
                @for (m of members().slice(0, 4); track m.id) {
                  <li>
                    <span class="ws-avatar" aria-hidden="true">{{ memberInitial(m) }}</span>
                    <div>
                      <p class="ws-row__title">
                        {{ memberLabel(m) }}
                        @if (m.user_id === currentUserId) {
                          <span class="ws-pill ws-pill--muted">Tú</span>
                        }
                      </p>
                      <p class="ws-row__meta">{{ memberRolesLabel(m) || 'Miembro' }} · {{ humanMemberStatus(m.status) }}</p>
                    </div>
                  </li>
                }
              </ul>
            }
            <div class="ws-inline-actions">
              @if (canInvite() && canManageMembers()) {
                <a [routerLink]="['/organizations', orgId(), 'invitations']">Invitar personas</a>
              }
              @if (canRoles() && canManageMembers()) {
                <a [routerLink]="['/organizations', orgId(), 'roles']">Roles y permisos</a>
              }
            </div>
          </section>

          <section class="ws-section" aria-label="Facturación">
            <div class="ws-section-head ws-section-head--compact">
              <div>
                <p class="ws-section__eyebrow">Plan y pagos</p>
                <h2 class="ws-section__heading">Facturación</h2>
              </div>
              <a class="ws-link" routerLink="/billing/invoices">Ver todo</a>
            </div>
            @if (!invoices().length) {
              <div class="ws-empty-state">
                <strong>Todo al día</strong>
                <span>No hay facturas registradas.</span>
              </div>
            } @else {
              <ul class="ws-rows">
                @for (inv of invoices().slice(0, 4); track inv.id) {
                  <li>
                    <div>
                      <p class="ws-row__title">{{ invoiceLabel(inv) }}</p>
                      <p class="ws-row__meta">{{ invoiceDate(inv) }}</p>
                    </div>
                    <div class="ws-row__side">
                      <span class="ws-invoice-amount">{{ formatMoney(inv.total, inv.currency) }}</span>
                      <span class="ws-pill" [class.ws-pill--warn]="invoiceTone(inv.status) === 'warn'" [class.ws-pill--danger]="invoiceTone(inv.status) === 'danger'" [class.ws-pill--muted]="invoiceTone(inv.status) === 'muted'">{{ humanInvoiceStatus(inv.status) }}</span>
                    </div>
                  </li>
                }
              </ul>
            }
            <div class="ws-inline-actions">
              <a routerLink="/subscriptions/overview">Plan y suscripción</a>
              <a routerLink="/billing/profile">Datos de facturación</a>
            </div>
          </section>
        </div>

        <section class="ws-section ws-section--profile" aria-label="Datos de la organización">
          <div class="ws-section-head ws-section-head--compact">
            <div>
              <p class="ws-section__eyebrow">Información del espacio</p>
              <h2 class="ws-section__heading">Datos de la organización</h2>
            </div>
            <a class="ws-link" [routerLink]="['/organizations', orgId(), 'settings']">Editar</a>
          </div>
          <dl class="ws-dl">
            <div><dt>Nombre legal</dt><dd>{{ org()?.legal_name || 'Sin registrar' }}</dd></div>
            <div><dt>País</dt><dd>{{ org()?.country_code || 'Sin registrar' }}</dd></div>
            <div><dt>Moneda</dt><dd>{{ org()?.default_currency || 'USD' }}</dd></div>
            <div><dt>Zona horaria</dt><dd>{{ org()?.timezone || 'Sin registrar' }}</dd></div>
          </dl>
          <div class="ws-inline-actions">
            @if (canAudit()) {
              <a [routerLink]="['/organizations', orgId(), 'audit']">Ver actividad</a>
            }
            <a routerLink="/compliance">Privacidad y cumplimiento</a>
          </div>
        </section>
      }
    </div>
  `,
})
export class OrgHubPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly spaces = inject(SpaceContextService);
  private readonly api = inject(OrganizationsApiService);
  private readonly billing = inject(BillingApiService);
  private readonly subs = inject(SubscriptionsApiService);
  private readonly auth = inject(AuthService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly org = signal<Organization | null>(null);
  readonly members = signal<Membership[]>([]);
  readonly invoices = signal<Invoice[]>([]);
  readonly memberTotal = signal(0);
  readonly invoiceTotal = signal(0);
  readonly subscription = signal<Subscription | null>(null);
  readonly planName = signal<string | null>(null);

  readonly pendingInvoiceCount = computed(
    () => this.invoices().filter((inv) => ['issued', 'draft', 'partially_paid', 'pending', 'past_due', 'failed'].includes((inv.status || '').toLowerCase())).length,
  );

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

  /** Members / invitations / roles tabs require operational organization tier. */
  canManageMembers(): boolean {
    const tier = this.spaces.productSurfaceContext().organizationTier;
    return tier === 'operational' || tier === 'recovery';
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
    const name = m.user?.display_name?.trim();
    if (name) return name;
    const email = m.user?.email?.trim();
    if (email) return email;
    return `Usuario ${m.user_id}`;
  }

  memberInitial(m: Membership): string {
    const value = this.memberLabel(m).trim();
    return (value[0] || 'M').toUpperCase();
  }

  memberRolesLabel(m: Membership): string | null {
    const roles = m.roles || [];
    if (!roles.length) return null;
    return roles.map((r) => this.humanRole(r.code || r.label)).join(', ');
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
      invoices: this.billing.listInvoices(id, { page: 1, page_size: 6 }).pipe(
        catchError(() => of({ items: [] as Invoice[], total: 0, page: 1, page_size: 6 })),
      ),
      subscriptions: this.subs.listSubscriptions(id, { page: 1, limit: 10 }).pipe(
        catchError(() => of({ items: [] as Subscription[] })),
      ),
      plans: this.subs.listPlans({ page: 1, limit: 50 }).pipe(catchError(() => of({ items: [] as Plan[] }))),
    }).subscribe({
      next: (res) => {
        const org = res.org || fromCtx || null;
        this.org.set(org);
        this.members.set(res.members.items || []);
        this.memberTotal.set(res.members.total || res.members.items?.length || 0);

        const invItems = res.invoices.items ?? [];
        this.invoices.set(invItems.slice(0, 6));
        this.invoiceTotal.set(res.invoices.total || invItems.length || 0);

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
