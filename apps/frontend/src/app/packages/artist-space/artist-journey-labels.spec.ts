import { LOCALE_EN } from '../../core/i18n/locales/en';
import { LOCALE_ES } from '../../core/i18n/locales/es';
import {
  ARTIST_ASSIGNABLE_ROLES,
  artistDiscoveryActionLabelKey,
  artistRelationshipLabelKey,
  artistRequestTypeLabelKey,
  artistRoleLabelKey,
  isHttpUrl,
} from './models/artist-space.models';

type LocaleKey = keyof typeof LOCALE_ES;

function es(key: string): string {
  return LOCALE_ES[key as LocaleKey];
}

function en(key: string): string {
  return LOCALE_EN[key as keyof typeof LOCALE_EN];
}

describe('artist journey human labels (051 · T004)', () => {
  it('maps membership roles to human labels in both locales', () => {
    expect(es(artistRoleLabelKey('owner'))).toBe('Propietario');
    expect(es(artistRoleLabelKey('administrator'))).toBe('Administrador');
    expect(es(artistRoleLabelKey('member'))).toBe('Colaborador');
    expect(es(artistRoleLabelKey('reader'))).toBe('Solo lectura');

    expect(en(artistRoleLabelKey('owner'))).toBe('Owner');
    expect(en(artistRoleLabelKey('administrator'))).toBe('Administrator');
    expect(en(artistRoleLabelKey('member'))).toBe('Collaborator');
    expect(en(artistRoleLabelKey('reader'))).toBe('Read only');
  });

  it('never leaves an assignable role without a translated label', () => {
    for (const role of ARTIST_ASSIGNABLE_ROLES) {
      const key = artistRoleLabelKey(role);
      expect(es(key)).toBeTruthy();
      expect(en(key)).toBeTruthy();
      expect(es(key)).not.toBe(role);
    }
  });

  it('falls back to an explicit unknown label instead of raw codes', () => {
    expect(artistRoleLabelKey('mystery')).toBe('artistSpace.role.unknown');
    expect(artistRequestTypeLabelKey('mystery')).toBe('artistSpace.request.type.unknown');
    expect(artistRelationshipLabelKey('mystery')).toBe('artistSpace.relationship.unknown');
    expect(es('artistSpace.role.unknown')).toBeTruthy();
  });

  it('translates every discovery action so the CTA never renders a backend code', () => {
    const actions = [
      'claim_ownership',
      'request_access',
      'open_space',
      'view_request',
      'none',
    ] as const;
    for (const action of actions) {
      const key = artistDiscoveryActionLabelKey(action);
      expect(es(key)).toBeTruthy();
      expect(en(key)).toBeTruthy();
    }
    expect(es(artistDiscoveryActionLabelKey('claim_ownership'))).toBe('Reclamar propiedad');
    expect(es(artistDiscoveryActionLabelKey('request_access'))).toBe('Solicitar acceso');
  });

  it('accepts only absolute http(s) URLs for evidence and profile links', () => {
    expect(isHttpUrl('https://example.com')).toBe(true);
    expect(isHttpUrl('http://example.com/path')).toBe(true);
    expect(isHttpUrl('example.com')).toBe(false);
    expect(isHttpUrl('javascript:alert(1)')).toBe(false);
    expect(isHttpUrl('')).toBe(false);
    expect(isHttpUrl(null)).toBe(false);
  });
});
