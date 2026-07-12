/** Central status/code → i18n key map. Internal codes stay unchanged. */

export const STATUS_LABEL_KEYS: Record<string, string> = {
  active: 'status.active',
  past_due: 'status.past_due',
  paid: 'status.paid',
  draft: 'status.draft',
  closed: 'status.closed',
  resolved: 'status.resolved',
  issued: 'status.issued',
  void: 'status.void',
  partially_paid: 'status.partially_paid',
  processing: 'status.processing',
  succeeded: 'status.succeeded',
  failed: 'status.failed',
  canceled: 'status.canceled',
  cancelled: 'status.canceled',
  trialing: 'status.trialing',
  expired: 'status.expired',
  pending: 'status.pending',
  open: 'status.open',
  limited: 'status.limited',
  blocked: 'status.blocked',
  grace: 'status.grace',
  recovered: 'status.recovered',
  suspended: 'status.suspended',
  archived: 'status.archived',
  approved: 'status.approved',
  published: 'status.published',
  rejected: 'status.rejected',
};

export function statusLabelKey(code: string | null | undefined): string {
  if (!code) return 'common.notAvailable';
  const normalized = String(code).trim().toLowerCase();
  return STATUS_LABEL_KEYS[normalized] ?? 'common.notAvailable';
}
