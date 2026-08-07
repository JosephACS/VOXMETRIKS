import { homePathForSpace, personalSpace, organizationSpace, dataOpsSpace } from './space.models';
import { spaceNavSectionsFor } from './space-nav.config';

describe('space models & nav (045)', () => {
  it('maps home paths per space kind', () => {
    expect(homePathForSpace(personalSpace())).toBe('/discover');
    expect(homePathForSpace(organizationSpace(3, 'Org'))).toBe('/organizations/3');
    expect(homePathForSpace(dataOpsSpace())).toBe('/elt-pipeline');
  });

  it('personal nav includes library activity without audio-features', () => {
    const paths = spaceNavSectionsFor('personal').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/discover');
    expect(paths).toContain('/activity');
    expect(paths).not.toContain('/audio-features');
    expect(paths).not.toContain('/recommendations');
  });

  it('organization nav includes hub and catalog routes', () => {
    const paths = spaceNavSectionsFor('organization', { organizationId: 5 }).flatMap((s) =>
      s.items.map((i) => i.path),
    );
    expect(paths).toContain('/organizations/5');
    expect(paths).toContain('/catalog');
    expect(paths).toContain('/artist-profiles');
  });

  it('data ops nav includes ELT and explorer', () => {
    const paths = spaceNavSectionsFor('data_ops').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/elt-pipeline');
    expect(paths).toContain('/explorer');
  });
});
