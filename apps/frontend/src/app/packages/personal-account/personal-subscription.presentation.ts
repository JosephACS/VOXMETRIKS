/** Map API owner_type codes to i18n keys without inventing commercial copy. */
export function personalOwnerTypeLabelKey(ownerType: string | null | undefined): string {
  const normalized = String(ownerType || '').trim().toLowerCase();
  if (normalized === 'user') return 'personal.subscription.owner.user';
  if (normalized === 'organization') return 'personal.subscription.owner.organization';
  return 'common.notAvailable';
}
