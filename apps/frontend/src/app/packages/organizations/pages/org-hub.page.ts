import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { OrganizationContextService } from '../services/organization-context.service';

/**
 * Spec 043 — Organización hub (perfil, miembros, invitaciones, auditoría).
 * Tabs live in module-context chrome; deep links preserved.
 */
@Component({
  selector: 'app-org-hub-page',
  standalone: true,
  imports: [CommonModule, RouterLink, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise org-hub">
      <app-enterprise-page-header
        [title]="orgName()"
        subtitle="Identidad, miembros y gobierno de la organización activa."
      />

      <div class="org-meta">
        <span class="org-chip">Estado: {{ statusLabel() }}</span>
        @if (orgId()) {
          <span class="org-chip muted">ID {{ orgId() }}</span>
        }
      </div>

      <div class="hub-grid">
        @for (card of cards(); track card.path) {
          <a class="hub-card" [routerLink]="card.path">
            <strong>{{ card.label }}</strong>
            <span>{{ card.hint }}</span>
          </a>
        }
      </div>
    </div>
  `,
  styles: [
    `
      .org-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: -0.35rem 0 1rem;
      }
      .org-chip {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        background: var(--accent-dim, rgba(30, 216, 150, 0.12));
        color: var(--accent, #1ed896);
      }
      .org-chip.muted {
        background: rgba(255, 255, 255, 0.06);
        color: var(--color-text-muted, rgba(255, 255, 255, 0.5));
      }
      .hub-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.75rem;
      }
      .hub-card {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        text-decoration: none;
        color: inherit;
        background: var(--color-surface, rgba(24, 24, 24, 0.92));
        border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.04));
      }
      .hub-card:hover {
        border-color: rgba(30, 216, 150, 0.28);
      }
      .hub-card span {
        font-size: 0.8125rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
      }
    `,
  ],
})
export class OrgHubPage {
  private readonly route = inject(ActivatedRoute);
  private readonly orgCtx = inject(OrganizationContextService);

  readonly orgId = computed(() => {
    const fromRoute = Number(this.route.snapshot.paramMap.get('id'));
    if (Number.isFinite(fromRoute) && fromRoute > 0) return fromRoute;
    return this.orgCtx.activeOrganization()?.id ?? null;
  });

  readonly orgName = computed(
    () => this.orgCtx.activeOrganization()?.display_name || 'Organización',
  );

  readonly statusLabel = computed(() => {
    const status = (this.orgCtx.activeOrganization() as { status?: string } | null)?.status;
    return status || this.orgCtx.accessTier() || 'activa';
  });

  readonly cards = computed(() => {
    const id = this.orgId();
    if (!id) return [] as { path: string; label: string; hint: string }[];
    return [
      { path: `/organizations/${id}/settings`, label: 'Perfil', hint: 'Datos e identidad' },
      { path: `/organizations/${id}/members`, label: 'Miembros', hint: 'Equipo y roles' },
      { path: `/organizations/${id}/invitations`, label: 'Invitaciones', hint: 'Accesos pendientes' },
      { path: `/organizations/${id}/audit`, label: 'Auditoría', hint: 'Historial de cambios' },
    ];
  });
}
