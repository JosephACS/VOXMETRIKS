import { Routes } from '@angular/router';
import {
  organizationModuleGuard,
  organizationRequiredGuard,
} from '../organizations/guards/organization.guards';

export const BILLING_ROUTES: Routes = [
  {
    path: 'billing',
    redirectTo: 'billing/invoices',
    pathMatch: 'full',
  },
  {
    path: 'billing/profile',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'billing.view')],
    loadComponent: () =>
      import('./pages/billing-profile.page').then((m) => m.BillingProfilePage),
    title: 'Perfil fiscal',
  },
  {
    path: 'billing/invoices',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'invoice.view')],
    loadComponent: () =>
      import('./pages/invoices-list.page').then((m) => m.InvoicesListPage),
    title: 'Facturas',
  },
  {
    path: 'billing/invoices/:id',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'invoice.view')],
    loadComponent: () =>
      import('./pages/invoice-detail.page').then((m) => m.InvoiceDetailPage),
    title: 'Detalle de factura',
  },
  {
    path: 'billing/payment-attempts',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'payment.view')],
    loadComponent: () =>
      import('./pages/payment-attempts.page').then((m) => m.PaymentAttemptsPage),
    title: 'Historial de cobros',
  },
  {
    path: 'billing/manual-transfer',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'payment.view')],
    loadComponent: () =>
      import('./pages/manual-transfer.page').then((m) => m.ManualTransferPage),
    title: 'Transferencia manual',
  },
  {
    path: 'billing/reconciliation',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'payment.view')],
    loadComponent: () =>
      import('./pages/reconciliation.page').then((m) => m.ReconciliationPage),
    title: 'Verificación de pagos',
  },
  {
    path: 'billing/refunds',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'payment.view')],
    loadComponent: () =>
      import('./pages/refunds.page').then((m) => m.RefundsPage),
    title: 'Reembolsos',
  },
  {
    path: 'billing/credit-notes',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'invoice.view')],
    loadComponent: () =>
      import('./pages/credit-notes.page').then((m) => m.CreditNotesPage),
    title: 'Notas de crédito',
  },
  {
    path: 'billing/ledger',
    canActivate: [organizationRequiredGuard, organizationModuleGuard('recovery', 'billing.view')],
    loadComponent: () =>
      import('./pages/ledger.page').then((m) => m.LedgerPage),
    title: 'Libro mayor',
  },
];
