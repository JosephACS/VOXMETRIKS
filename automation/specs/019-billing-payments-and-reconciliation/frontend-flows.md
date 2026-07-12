# Frontend Flows — Spec 019

## Pages (Angular standalone)

### BillingProfileComponent
- Route: `/billing/profile`
- Shows/creates billing profile
- Currency, legal name, tax ID, address, email
- Edit mode for billing.manage users

### InvoicesListComponent
- Route: `/billing/invoices`
- Paginated table with status badges
- Filter by status
- Past-due banner if any invoice is past_due or subscription.access_state=limited

### InvoiceDetailComponent
- Route: `/billing/invoices/:id`
- Shows items, amounts, status, credit notes applied
- Issue / Void actions for permitted users

### PaymentAttemptsComponent
- Route: `/billing/payment-attempts`
- List with provider, amount, status
- `[MOCK]` badge for academic_mock attempts

### ManualTransferComponent
- Route: `/billing/manual-transfer`
- Form: select invoice, enter reference, amount
- Submits manual transfer + confirms

### ReconciliationComponent
- Route: `/billing/reconciliation`
- List payments pending reconciliation
- Reconcile / settle actions

### RefundsComponent
- Route: `/billing/refunds`
- List refunds
- Create refund form (select payment, amount, reason)

### CreditNotesComponent
- Route: `/billing/credit-notes`
- List credit notes
- Create + apply credit note

### LedgerComponent
- Route: `/billing/ledger`
- Read-only append-only ledger view
- Filter by date range, entry_type

### PastDueBannerComponent
- Shared component shown at org level
- Visible when subscription access_state=limited

## Navigation
- Billing menu group in org sidebar (visible to billing.view)
- Sub-items: Profile, Invoices, Payments, Transfers, Reconciliation, Refunds, Credit Notes, Ledger

## Service: BillingService
- `getProfile()`, `createProfile()`, `updateProfile()`
- `listInvoices()`, `createInvoice()`, `issueInvoice()`, `voidInvoice()`
- `listPayments()`, `settlePayment()`, `reconcilePayment()`, `allocatePayment()`
- `createPaymentAttempt()`, `confirmAttempt()`, `createManualTransfer()`
- `listRefunds()`, `createRefund()`
- `listCreditNotes()`, `createCreditNote()`, `applyCreditNote()`
- `getLedger()`
