import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { canAccessArtistPermission } from './models/artist-space.models';

const here = dirname(fileURLToPath(import.meta.url));

describe('artist invitation accept security (046 hotfix)', () => {
  it('API acceptInvitation posts token in body, not URL path', () => {
    const src = readFileSync(resolve(here, './services/artist-space-api.service.ts'), 'utf8');
    expect(src).toContain('`${BASE}/artist-invitations/accept`');
    expect(src).toContain('{ token }');
    expect(src).not.toMatch(/artist-invitations\/\$\{.*token.*\}\/accept/);
    expect(src).not.toContain('encodeURIComponent(token)');
  });

  it('accept route has no :token path param', () => {
    const src = readFileSync(resolve(here, './artist-space.routes.ts'), 'utf8');
    expect(src).toContain("path: 'artist-invitations/accept'");
    expect(src).not.toContain('artist-invitations/:token/accept');
  });

  it('accept page source does not read route token param', () => {
    const src = readFileSync(resolve(here, './pages/artist-invite-accept.page.ts'), 'utf8');
    expect(src).not.toContain('paramMap');
    expect(src).not.toContain("get('token')");
    expect(src).not.toContain('ActivatedRoute');
  });

  it('invite capability is distinct from team.manage', () => {
    const inviteOnly = ['artist_space.view', 'artist_space.invite'];
    expect(canAccessArtistPermission(inviteOnly, 'artist_space.invite')).toBe(true);
    expect(canAccessArtistPermission(inviteOnly, 'artist_space.team.manage')).toBe(false);
    expect(canAccessArtistPermission(['artist_space.view'], 'artist_space.invite')).toBe(false);
  });
});
