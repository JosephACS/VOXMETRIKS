import { OrganizationJourney } from '../models/organization.models';

/** Spec 053 — server next_action drives CTA surfaces (unit-level). */
describe('organization journey next_action mapping', () => {
  function primaryCta(j: Pick<OrganizationJourney, 'next_action' | 'capabilities'>): string {
    switch (j.next_action) {
      case 'review_profile':
        return 'profile';
      case 'choose_plan':
      case 'resume_checkout':
      case 'await_payment':
        return 'plan';
      case 'invite_team':
        return 'team';
      case 'complete':
        return 'complete';
      case 'enter_workspace':
        return 'hub';
      case 'wait_for_owner':
        return 'wait';
      case 'organization_unavailable':
        return 'unavailable';
      default: {
        const _exhaustive: never = j.next_action as never;
        return String(_exhaustive);
      }
    }
  }

  it('maps choose_plan to plan CTA', () => {
    expect(
      primaryCta({
        next_action: 'choose_plan',
        capabilities: {
          update_profile: true,
          choose_plan: true,
          resume_checkout: false,
          invite_team: true,
          view_members: true,
          enter_workspace: false,
          complete_journey: false,
        },
      }),
    ).toBe('plan');
  });

  it('maps wait_for_owner for invited members', () => {
    expect(
      primaryCta({
        next_action: 'wait_for_owner',
        capabilities: {
          update_profile: false,
          choose_plan: false,
          resume_checkout: false,
          invite_team: false,
          view_members: true,
          enter_workspace: false,
          complete_journey: false,
        },
      }),
    ).toBe('wait');
  });

  it('does not invent operational access from checkout UI alone', () => {
    const j: OrganizationJourney['capabilities'] = {
      update_profile: true,
      choose_plan: false,
      resume_checkout: true,
      invite_team: false,
      view_members: true,
      enter_workspace: false,
      complete_journey: false,
    };
    expect(j.enter_workspace).toBe(false);
    expect(primaryCta({ next_action: 'resume_checkout', capabilities: j })).toBe('plan');
  });
});
