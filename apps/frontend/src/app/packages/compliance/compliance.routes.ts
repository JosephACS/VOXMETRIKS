import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const COMPLIANCE_ROUTES: Routes = [
  {
    path: 'compliance',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'compliance.view'),
    ],
    loadComponent: () => import('./pages/privacy-center.page').then((m) => m.PrivacyCenterPage),
    title: 'Centro de privacidad',
  },
  {
    path: 'compliance/admin',
    canActivate: [
      organizationRequiredGuard,
      organizationModuleGuard('operational', 'compliance.manage'),
    ],
    loadComponent: () => import('./pages/compliance-admin.page').then((m) => m.ComplianceAdminPage),
    title: 'Administración de cumplimiento',
  },
];
