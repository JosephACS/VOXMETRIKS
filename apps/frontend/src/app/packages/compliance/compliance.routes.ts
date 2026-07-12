import { Routes } from '@angular/router';

export const COMPLIANCE_ROUTES: Routes = [
  { path: 'compliance', loadComponent: () => import('./pages/privacy-center.page').then(m => m.PrivacyCenterPage), title: 'Privacy Center' },
  { path: 'compliance/admin', loadComponent: () => import('./pages/compliance-admin.page').then(m => m.ComplianceAdminPage), title: 'Compliance Admin' },
];
