import { Routes } from '@angular/router';

export const BILLING_ROUTES: Routes = [
  {
    path: 'billing',
    redirectTo: 'billing/invoices',
    pathMatch: 'full',
  },
  {
    path: 'billing/profile',
    loadComponent: () =>
      import('./pages/billing-profile.page').then((m) => m.BillingProfilePage),
    title: 'Perfil fiscal',
  },
  {
    path: 'billing/invoices',
    loadComponent: () =>
      import('./pages/invoices-list.page').then((m) => m.InvoicesListPage),
    title: 'Facturas',
  },
  {
    path: 'billing/invoices/:id',
    loadComponent: () =>
      import('./pages/invoice-detail.page').then((m) => m.InvoiceDetailPage),
    title: 'Detalle de factura',
  },
  {
    path: 'billing/payment-attempts',
    loadComponent: () =>
      import('./pages/payment-attempts.page').then((m) => m.PaymentAttemptsPage),
    title: 'Intentos de pago',
  },
  {
    path: 'billing/manual-transfer',
    loadComponent: () =>
      import('./pages/manual-transfer.page').then((m) => m.ManualTransferPage),
    title: 'Transferencia manual',
  },
  {
    path: 'billing/reconciliation',
    loadComponent: () =>
      import('./pages/reconciliation.page').then((m) => m.ReconciliationPage),
    title: 'Conciliación',
  },
  {
    path: 'billing/refunds',
    loadComponent: () =>
      import('./pages/refunds.page').then((m) => m.RefundsPage),
    title: 'Reembolsos',
  },
  {
    path: 'billing/credit-notes',
    loadComponent: () =>
      import('./pages/credit-notes.page').then((m) => m.CreditNotesPage),
    title: 'Notas de crédito',
  },
  {
    path: 'billing/ledger',
    loadComponent: () =>
      import('./pages/ledger.page').then((m) => m.LedgerPage),
    title: 'Libro mayor',
  },
];
