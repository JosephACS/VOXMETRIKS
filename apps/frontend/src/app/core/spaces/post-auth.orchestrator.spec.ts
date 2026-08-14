import {
  extractInvitationNavigation,
  resolvePostAuthPath,
  returnUrlAllowedForManifest,
} from './post-auth.orchestrator';
import { kindRequiredByPath, type SessionBootstrap } from './session-bootstrap.model';

function manifest(overrides: Partial<SessionBootstrap> = {}): SessionBootstrap {
  return {
    user: { id: 1, display_name: 'Alex', identity_role: 'user' },
    security: { email_verified: true, profile_pin_enabled: false },
    spaces: [
      {
        key: 'personal',
        kind: 'personal',
        display_name: 'Personal',
        capabilities: [{ code: 'music.listen', allowed: true, reason: null }],
        home_path: '/discover',
      },
    ],
    active_space_key: 'personal',
    pending_actions: [],
    recommended_path: '/discover',
    ...overrides,
  };
}

describe('post-auth orchestrator (050)', () => {
  it('restores an authorized local returnUrl', () => {
    const m = manifest();
    expect(returnUrlAllowedForManifest('/discover', m)).toBe(true);
    expect(
      resolvePostAuthPath({ manifest: m, returnUrl: '/discover', householdPath: null }),
    ).toBe('/discover');
  });

  it('ignores unauthorized org destinations when the user has no org space', () => {
    const m = manifest();
    expect(returnUrlAllowedForManifest('/billing/invoices', m)).toBe(false);
    expect(
      resolvePostAuthPath({
        manifest: m,
        returnUrl: '/billing/invoices',
        householdPath: null,
      }),
    ).toBe('/discover');
  });

  it('asks to choose when multiple spaces and no destination', () => {
    const m = manifest({
      spaces: [
        ...manifest().spaces,
        {
          key: 'organization:9',
          kind: 'organization',
          display_name: 'Studio',
          capabilities: [{ code: 'organization.view', allowed: true, reason: null }],
          home_path: '/workpanel',
        },
      ],
      pending_actions: [{ code: 'choose_space' }],
      recommended_path: '/discover',
    });
    expect(
      resolvePostAuthPath({ manifest: m, returnUrl: null, householdPath: null }),
    ).toBe('/welcome/spaces');
  });

  it('routes first-run ordinary accounts to welcome', () => {
    const m = manifest({ pending_actions: [{ code: 'first_run' }] });
    expect(
      resolvePostAuthPath({ manifest: m, returnUrl: null, householdPath: null }),
    ).toBe('/welcome');
  });

  it('allows invitation acceptance before any membership space exists', () => {
    const m = manifest();
    const orgInvite = '/invitations/accept?token=abc123';
    const artistInvite = '/artist-invitations/accept?token=def456';

    expect(kindRequiredByPath(orgInvite)).toBeNull();
    expect(kindRequiredByPath(artistInvite)).toBeNull();
    expect(returnUrlAllowedForManifest(orgInvite, m)).toBe(true);
    expect(returnUrlAllowedForManifest(artistInvite, m)).toBe(true);
    expect(
      resolvePostAuthPath({ manifest: m, returnUrl: orgInvite, householdPath: null }),
    ).toBe(orgInvite);
    expect(
      resolvePostAuthPath({ manifest: m, returnUrl: artistInvite, householdPath: null }),
    ).toBe(artistInvite);
  });

  it('keeps requiring an artist space for artist workspace destinations', () => {
    const m = manifest();
    expect(kindRequiredByPath('/artist-space/tracks')).toBe('artist');
    expect(returnUrlAllowedForManifest('/artist-space/tracks', m)).toBe(false);
  });

  it('does not divert invitation destinations to the household chooser', () => {
    const m = manifest();
    expect(
      resolvePostAuthPath({
        manifest: m,
        returnUrl: '/invitations/accept?token=abc123',
        householdPath: '/account/profiles',
      }),
    ).toBe('/invitations/accept?token=abc123');
  });

  it('moves invitation credentials out of the destination URL', () => {
    expect(extractInvitationNavigation('/artist-invitations/accept?token=abc123')).toEqual({
      path: '/artist-invitations/accept',
      invitationToken: 'abc123',
    });
    expect(extractInvitationNavigation('/discover?token=abc123')).toBeNull();
  });

  it('applies household chooser only for Personal destinations', () => {
    const withOrg = manifest({
      spaces: [
        ...manifest().spaces,
        {
          key: 'organization:2',
          kind: 'organization',
          display_name: 'Org',
          capabilities: [{ code: 'organization.view', allowed: true, reason: null }],
          home_path: '/workpanel',
        },
      ],
    });
    expect(
      resolvePostAuthPath({
        manifest: withOrg,
        returnUrl: '/workpanel',
        householdPath: '/account/profiles',
      }),
    ).toBe('/workpanel');
    expect(
      resolvePostAuthPath({
        manifest: withOrg,
        returnUrl: '/discover',
        householdPath: '/account/profiles',
      }),
    ).toBe('/account/profiles');
  });
});
