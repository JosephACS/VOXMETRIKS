export interface SessionCapability {
  code: string;
  allowed: boolean;
  reason: string | null;
}

export interface SessionSpace {
  key: string;
  kind: 'personal' | 'organization' | 'artist' | 'data_ops' | 'platform_admin';
  display_name: string;
  capabilities: SessionCapability[];
  home_path: string;
}

export interface SessionPendingAction {
  code: string;
}

export interface SessionBootstrap {
  user: {
    id: number;
    display_name: string;
    identity_role: string;
  };
  security: {
    email_verified: boolean;
    profile_pin_enabled: boolean;
  };
  spaces: SessionSpace[];
  active_space_key: string;
  pending_actions: SessionPendingAction[];
  recommended_path: string;
}

/** Raised when the session manifest could not be loaded — never synthesize spaces instead. */
export class SessionBootstrapError extends Error {
  constructor(
    readonly reason: string,
    readonly unauthorized = false,
  ) {
    super(reason);
    this.name = 'SessionBootstrapError';
  }
}

export function spaceKindFromKey(
  key: string,
): SessionSpace['kind'] | null {
  if (key === 'personal' || key === 'data_ops' || key === 'platform_admin') return key;
  if (key.startsWith('organization:')) return 'organization';
  if (key.startsWith('artist:')) return 'artist';
  return null;
}

export function kindRequiredByPath(path: string): SessionSpace['kind'] | null {
  const p = (path || '').split('?')[0];
  // Invitation acceptance happens BEFORE membership exists, so it cannot require a space.
  if (p.startsWith('/invitations/accept') || p.startsWith('/artist-invitations/accept')) {
    return null;
  }
  if (p.startsWith('/artist-space')) {
    return 'artist';
  }
  if (p.startsWith('/elt-pipeline') || p.startsWith('/etl-pipeline') || p === '/explorer') {
    return 'data_ops';
  }
  if (p.startsWith('/platform-ops') || p.startsWith('/crm')) {
    return 'platform_admin';
  }
  if (
    p.startsWith('/organizations') ||
    p.startsWith('/business') ||
    p.startsWith('/billing') ||
    p.startsWith('/subscriptions') ||
    p.startsWith('/campaigns') ||
    p.startsWith('/royalties') ||
    p.startsWith('/workpanel') ||
    p.startsWith('/catalog') ||
    p.startsWith('/reports')
  ) {
    return 'organization';
  }
  if (
    p.startsWith('/discover') ||
    p.startsWith('/search') ||
    p.startsWith('/tracks') ||
    p.startsWith('/liked') ||
    p.startsWith('/history') ||
    p.startsWith('/playlists') ||
    p.startsWith('/account') ||
    p === '/settings'
  ) {
    return 'personal';
  }
  return null;
}

export function pendingHas(manifest: SessionBootstrap, code: string): boolean {
  return (manifest.pending_actions || []).some((a) => a.code === code);
}
