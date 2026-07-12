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
    title: 'Billing Profile',
  },
  {
    path: 'billing/invoices',
    loadComponent: () =>
      import('./pages/invoices-list.page').then((m) => m.InvoicesListPage),
    title: 'Invoices',
  },
  {
    path: 'billing/invoices/:id',
    loadComponent: () =>
      import('./pages/invoice-detail.page').then((m) => m.InvoiceDetailPage),
    title: 'Invoice Detail',
  },
  {
    path: 'billing/payment-attempts',
    loadComponent: () =>
      import('./pages/payment-attempts.page').then((m) => m.PaymentAttemptsPage),
    title: 'Payment Attempts',
  },
  {
    path: 'billing/manual-transfer',
    loadComponent: () =>
      import('./pages/manual-transfer.page').then((m) => m.ManualTransferPage),
    title: 'Manual Transfer',
  },
  {
    path: 'billing/reconciliation',
    loadComponent: () =>
      import('./pages/reconciliation.page').then((m) => m.ReconciliationPage),
    title: 'Reconciliation',
  },
  {
    path: 'billing/refunds',
    loadComponent: () =>
      import('./pages/refunds.page').then((m) => m.RefundsPage),
    title: 'Refunds',
  },
  {
    path: 'billing/credit-notes',
    loadComponent: () =>
      import('./pages/credit-notes.page').then((m) => m.CreditNotesPage),
    title: 'Credit Notes',
  },
  {
    path: 'billing/ledger',
    loadComponent: () =>
      import('./pages/ledger.page').then((m) => m.LedgerPage),
    title: 'Billing Ledger',
  },
];
