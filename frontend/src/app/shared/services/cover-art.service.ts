import { Injectable } from '@angular/core';

// Paleta neutra y sobria (tonos apagados, sin verdes chillones).
// Cada gradiente es oscuro con un tinte sutil para dar variedad discreta.
const GRADIENTS = [
  'linear-gradient(145deg, #2a2d34 0%, #16181c 100%)',
  'linear-gradient(145deg, #2e2a33 0%, #18161c 100%)',
  'linear-gradient(145deg, #26303a 0%, #15191e 100%)',
  'linear-gradient(145deg, #313037 0%, #1a191e 100%)',
  'linear-gradient(145deg, #2b3330 0%, #16191a 100%)',
  'linear-gradient(145deg, #343033 0%, #1c1a1c 100%)',
  'linear-gradient(145deg, #2a2e38 0%, #15171c 100%)',
  'linear-gradient(145deg, #38332e 0%, #1c1a17 100%)',
  'linear-gradient(145deg, #2d2d2d 0%, #161616 100%)',
  'linear-gradient(145deg, #283038 0%, #14171b 100%)',
];

@Injectable({ providedIn: 'root' })
export class CoverArtService {
  gradientFor(id: number | string): string {
    const n = typeof id === 'number' ? id : this.hash(id);
    return GRADIENTS[Math.abs(n) % GRADIENTS.length];
  }

  /** Primera letra visible para portadas sin imagen. */
  initialFor(text?: string | null): string {
    const t = text?.trim();
    if (!t) return '?';
    return t.charAt(0).toUpperCase();
  }

  /** Iniciales (p. ej. artista: "Dua Lipa" → "DL"). */
  initialsFor(text?: string | null, max = 2): string {
    const t = text?.trim();
    if (!t) return '?';
    const parts = t.split(/\s+/).filter(Boolean);
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
    return parts
      .slice(0, max)
      .map((p) => p.charAt(0).toUpperCase())
      .join('');
  }

  private hash(s: string): number {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i);
    return h;
  }
}
