/**
 * Voxmetrik — Motion constants for TypeScript / Angular animations.
 * Mirror of CSS tokens in `src/styles/motion.css`. Do not hardcode durations elsewhere.
 */

export const MOTION_DURATION = {
  instant: 0,
  fast: 120,
  normal: 170,
  slow: 230,
  slower: 300,
} as const;

export const MOTION_EASING = {
  standard: 'cubic-bezier(0.2, 0.82, 0.2, 1)',
  out: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
  inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
} as const;

export const MOTION_DISTANCE = {
  xs: 2,
  sm: 4,
  md: 8,
  lg: 12,
} as const;

export type MotionDurationKey = keyof typeof MOTION_DURATION;
export type MotionEasingKey = keyof typeof MOTION_EASING;

/** Build an Angular `animate()` timing string from tokens. */
export function motionTiming(
  duration: MotionDurationKey = 'normal',
  easing: MotionEasingKey = 'standard',
): string {
  return `${MOTION_DURATION[duration]}ms ${MOTION_EASING[easing]}`;
}

/** Standard route / panel enter animation timing. */
export const MOTION_ROUTE_ENTER = motionTiming('normal', 'standard');
