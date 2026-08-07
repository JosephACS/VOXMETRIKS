/**
 * Shell layout tokens for the fixed global player clearance.
 * Keep CSS (`styles.css`, dashboard-layout, player-bar) aligned with these values.
 */
export const SHELL_PLAYER_HEIGHT_DESKTOP_PX = 88;
export const SHELL_PLAYER_HEIGHT_MOBILE_PX = 72;
export const SHELL_NAV_PLAYER_EXTRA_GAP_PX = 16;

/** Padding under the scrollable sidebar nav so the last item clears the player. */
export function sidebarNavPlayerClearance(
  playerHeightCss = 'var(--player-height)',
  extraGapPx = SHELL_NAV_PLAYER_EXTRA_GAP_PX,
): string {
  return `calc(${playerHeightCss} + ${extraGapPx}px + env(safe-area-inset-bottom, 0px))`;
}
