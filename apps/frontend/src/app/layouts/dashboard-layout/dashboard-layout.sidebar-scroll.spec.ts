import {
  SHELL_NAV_PLAYER_EXTRA_GAP_PX,
  SHELL_PLAYER_HEIGHT_DESKTOP_PX,
  SHELL_PLAYER_HEIGHT_MOBILE_PX,
  sidebarNavPlayerClearance,
} from './shell-layout.tokens';

describe('shell layout player clearance', () => {
  it('exposes stable desktop/mobile player heights', () => {
    expect(SHELL_PLAYER_HEIGHT_DESKTOP_PX).toBe(88);
    expect(SHELL_PLAYER_HEIGHT_MOBILE_PX).toBe(72);
    expect(SHELL_NAV_PLAYER_EXTRA_GAP_PX).toBe(16);
  });

  it('builds the shared nav padding formula used by the sidebar', () => {
    expect(sidebarNavPlayerClearance()).toBe(
      'calc(var(--player-height) + 16px + env(safe-area-inset-bottom, 0px))',
    );
  });
});
