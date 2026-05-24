import { Injectable } from '@angular/core';

const GRADIENTS = [
  'linear-gradient(135deg, #1ed896 0%, #0d3d2e 100%)',
  'linear-gradient(135deg, #148f5e 0%, #121212 100%)',
  'linear-gradient(135deg, #1db954 0%, #004225 100%)',
  'linear-gradient(135deg, #2dd4bf 0%, #134e4a 100%)',
  'linear-gradient(135deg, #34d399 0%, #064e3b 100%)',
  'linear-gradient(135deg, #6ee7b7 0%, #1e293b 100%)',
  'linear-gradient(135deg, #059669 0%, #000000 100%)',
  'linear-gradient(135deg, #10b981 0%, #312e81 55%, #000 100%)',
  'linear-gradient(160deg, #1ed896 0%, #181818 50%, #000 100%)',
  'linear-gradient(145deg, #065f46 0%, #1ed896 100%)',
];

@Injectable({ providedIn: 'root' })
export class CoverArtService {
  gradientFor(id: number | string): string {
    const n = typeof id === 'number' ? id : this.hash(id);
    return GRADIENTS[Math.abs(n) % GRADIENTS.length];
  }

  private hash(s: string): number {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i);
    return h;
  }
}
