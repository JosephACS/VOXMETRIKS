import { Routes } from '@angular/router';
import { crmAccessGuard } from './guards/crm.guards';

export const CRM_ROUTES: Routes = [
  {
    path: 'crm/access-denied',
    title: 'CRM — Acceso denegado',
    loadComponent: () =>
      import('./pages/crm-access-denied.page').then((m) => m.CrmAccessDeniedPageComponent),
  },
  {
    path: 'crm',
    redirectTo: 'crm/dashboard',
    pathMatch: 'full',
  },
  {
    path: 'crm/dashboard',
    title: 'CRM — Panel',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-dashboard.page').then((m) => m.CrmDashboardPageComponent),
  },
  {
    path: 'crm/prospects',
    title: 'CRM — Prospectos',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-prospects-list.page').then((m) => m.CrmProspectsListPageComponent),
  },
  {
    path: 'crm/prospects/:id',
    title: 'CRM — Prospecto',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-prospect-detail.page').then((m) => m.CrmProspectDetailPageComponent),
  },
  {
    path: 'crm/opportunities',
    title: 'CRM — Oportunidades',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-opportunity-board.page').then((m) => m.CrmOpportunityBoardPageComponent),
  },
  {
    path: 'crm/opportunities/:id',
    title: 'CRM — Oportunidad',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-opportunity-detail.page').then(
        (m) => m.CrmOpportunityDetailPageComponent,
      ),
  },
  {
    path: 'crm/opportunities/:id/lost',
    title: 'CRM — Oportunidad cerrada',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-lost-opportunity.page').then((m) => m.CrmLostOpportunityPageComponent),
  },
  {
    path: 'crm/quotations/:id',
    title: 'CRM — Cotización',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-quotation-editor.page').then((m) => m.CrmQuotationEditorPageComponent),
  },
  {
    path: 'crm/approvals',
    title: 'CRM — Aprobaciones',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-approvals.page').then((m) => m.CrmApprovalsPageComponent),
  },
  {
    path: 'crm/contracts/:id',
    title: 'CRM — Contrato',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-contract-detail.page').then((m) => m.CrmContractDetailPageComponent),
  },
  {
    path: 'crm/conversions/:id',
    title: 'CRM — Conversión',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-conversion-wizard.page').then((m) => m.CrmConversionWizardPageComponent),
  },
  {
    path: 'crm/audit',
    title: 'CRM — Auditoría',
    canActivate: [crmAccessGuard],
    loadComponent: () =>
      import('./pages/crm-audit.page').then((m) => m.CrmAuditPageComponent),
  },
];
