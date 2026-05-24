import { trigger, transition, style, animate, query } from '@angular/animations';

/** Transición suave entre rutas — solo el contenido, sin recargar el layout. */
export const routeFadeAnimation = trigger('routeFade', [
  transition('* <=> *', [
    query(':enter', [
      style({ opacity: 0, transform: 'translateY(8px)' }),
      animate('320ms cubic-bezier(0.22, 1, 0.36, 1)', style({ opacity: 1, transform: 'translateY(0)' })),
    ], { optional: true }),
  ]),
]);
