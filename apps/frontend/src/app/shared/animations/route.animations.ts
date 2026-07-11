import { trigger, transition, style, animate, query } from '@angular/animations';
import { MOTION_DISTANCE, MOTION_ROUTE_ENTER } from '../motion/motion.constants';

/** Transición suave entre rutas — solo el contenido, sin recargar el layout. */
export const routeFadeAnimation = trigger('routeFade', [
  transition('* <=> *', [
    query(':enter', [
      style({ opacity: 0, transform: `translateY(${MOTION_DISTANCE.md}px)` }),
      animate(MOTION_ROUTE_ENTER, style({ opacity: 1, transform: 'translateY(0)' })),
    ], { optional: true }),
  ]),
]);
