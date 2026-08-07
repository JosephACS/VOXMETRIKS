import { Routes } from '@angular/router';
import {
  organizationPathContextGuard,
  organizationModuleGuard,
  organizationRequiredGuard,
} from './guards/organization.guards';

export const ORGANIZATIONS_ROUTES: Routes = [
  {
    path: 'business',
    title: 'VOXMETRIKS para empresas',
    loadComponent: () =>
      import('./pages/business-for-enterprises.page').then(
        (m) => m.BusinessForEnterprisesPageComponent,
      ),
  },
  {
    path: 'organizations/new',
    title: 'Crear organización',
    loadComponent: () =>
      import('./pages/org-create.page').then((m) => m.OrgCreatePageComponent),
  },
  {
    path: 'organizations/onboarding',
    title: 'Onboarding organización',
    canActivate: [organizationRequiredGuard],
    loadComponent: () =>
      import('./pages/org-onboarding.page').then((m) => m.OrgOnboardingPageComponent),
  },
  {
    path: 'organizations/none',
    title: 'Sin organización',
    loadComponent: () =>
      import('./pages/org-none.page').then((m) => m.OrgNonePageComponent),
  },
  {
    path: 'organizations/suspended',
    title: 'Organización suspendida',
    loadComponent: () =>
      import('./pages/org-suspended.page').then((m) => m.OrgSuspendedPageComponent),
  },
  {
    path: 'organizations/closed',
    title: 'Organización cerrada',
    loadComponent: () =>
      import('./pages/org-closed.page').then((m) => m.OrgClosedPageComponent),
  },
  {
    path: 'organizations/:id',
    title: 'Organización',
    canActivate: [
      organizationPathContextGuard,
      organizationModuleGuard('org_admin_basic', 'organization.view'),
    ],
    pathMatch: 'full',
    loadComponent: () =>
      import('./pages/org-hub.page').then((m) => m.OrgHubPage),
  },
  {
    path: 'organizations/:id/settings',
    title: 'Perfil organización',
    canActivate: [
      organizationPathContextGuard,
      organizationModuleGuard('org_admin_basic', 'organization.view'),
    ],
    loadComponent: () =>
      import('./pages/org-settings.page').then((m) => m.OrgSettingsPageComponent),
  },
  {
    path: 'organizations/:id/members',
    title: 'Miembros',
    canActivate: [
      organizationPathContextGuard,
      organizationModuleGuard('org_admin_advanced', 'member.view'),
    ],
    loadComponent: () =>
      import('./pages/org-members.page').then((m) => m.OrgMembersPageComponent),
  },
  {
    path: 'organizations/:id/invitations',
    title: 'Invitaciones',
    canActivate: [
      organizationPathContextGuard,
      organizationModuleGuard('org_admin_advanced', 'member.invite'),
    ],
    loadComponent: () =>
      import('./pages/org-invitations.page').then((m) => m.OrgInvitationsPageComponent),
  },
  {
    path: 'organizations/:id/roles',
    title: 'Roles',
    canActivate: [
      organizationPathContextGuard,
      organizationModuleGuard('org_admin_advanced', 'role.view'),
    ],
    loadComponent: () =>
      import('./pages/org-roles.page').then((m) => m.OrgRolesPageComponent),
  },
  {
    path: 'organizations/:id/audit',
    title: 'Auditoría',
    canActivate: [
      organizationPathContextGuard,
      organizationModuleGuard('org_admin_advanced', 'audit.view'),
    ],
    loadComponent: () =>
      import('./pages/org-audit.page').then((m) => m.OrgAuditPageComponent),
  },
  {
    path: 'access-denied',
    title: 'Acceso denegado',
    loadComponent: () =>
      import('./pages/org-access-denied.page').then((m) => m.OrgAccessDeniedPageComponent),
  },
  {
    path: 'invitations/accept',
    title: 'Aceptar invitación',
    loadComponent: () =>
      import('./pages/org-accept-invite.page').then((m) => m.OrgAcceptInvitePageComponent),
  },
  // Path-param token route removed in I5 (URL/Referer exposure). Use query ?token= or paste.
];
