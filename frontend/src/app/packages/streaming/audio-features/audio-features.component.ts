import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricBarComponent } from '../../../shared/components/metric-bar/metric-bar.component';

interface AudioFeatureTrack {
  id: number;
  nombre: string;
  artista: string;
  popularity: number;
  danceability: number;
  energy: number;
  valence: number;
  acousticness: number;
  speechiness: number;
  instrumentalness: number;
  liveness: number;
}

interface FeatureDef {
  key: keyof AudioFeatureTrack;
  label: string;
  color: string;
}

@Component({
  selector: 'app-audio-features',
  standalone: true,
  imports: [CommonModule, MetricBarComponent],
  templateUrl: './audio-features.component.html',
  styleUrls: ['./audio-features.component.css'],
})
export class AudioFeaturesComponent {
  featureDefs: FeatureDef[] = [
    { key: 'danceability', label: 'Bailabilidad', color: '#1ed896' },
    { key: 'energy', label: 'Energía', color: '#7c3aed' },
    { key: 'valence', label: 'Valencia', color: '#10b981' },
    { key: 'acousticness', label: 'Acústica', color: '#3b82f6' },
    { key: 'speechiness', label: 'Locución', color: '#f59e0b' },
    { key: 'instrumentalness', label: 'Instrumental', color: '#ec4899' },
    { key: 'liveness', label: 'En vivo', color: '#6366f1' },
  ];

  tracks = signal<AudioFeatureTrack[]>([
    {
      id: 1, nombre: 'Blinding Lights', artista: 'The Weeknd',
      popularity: 89, danceability: 0.73, energy: 0.84, valence: 0.56,
      acousticness: 0.001, speechiness: 0.05, instrumentalness: 0.0, liveness: 0.09,
    },
    {
      id: 2, nombre: 'Levitating', artista: 'Dua Lipa',
      popularity: 85, danceability: 0.83, energy: 0.83, valence: 0.84,
      acousticness: 0.002, speechiness: 0.06, instrumentalness: 0.0, liveness: 0.09,
    },
    {
      id: 3, nombre: 'Shape of You', artista: 'Ed Sheeran',
      popularity: 82, danceability: 0.76, energy: 0.65, valence: 0.93,
      acousticness: 0.58, speechiness: 0.09, instrumentalness: 0.0, liveness: 0.09,
    },
    {
      id: 4, nombre: 'Starboy', artista: 'The Weeknd',
      popularity: 78, danceability: 0.68, energy: 0.59, valence: 0.48,
      acousticness: 0.14, speechiness: 0.05, instrumentalness: 0.0, liveness: 0.14,
    },
    {
      id: 5, nombre: 'Bad Guy', artista: 'Billie Eilish',
      popularity: 76, danceability: 0.70, energy: 0.43, valence: 0.56,
      acousticness: 0.10, speechiness: 0.38, instrumentalness: 0.13, liveness: 0.10,
    },
  ]);

  selectedId = signal(1);

  selectedTrack = computed(() =>
    this.tracks().find((t) => t.id === this.selectedId()) ?? this.tracks()[0]
  );

  avgEnergy = computed(() => {
    const t = this.tracks();
    return +(t.reduce((s, x) => s + x.energy, 0) / t.length).toFixed(2);
  });

  avgDanceability = computed(() => {
    const t = this.tracks();
    return +(t.reduce((s, x) => s + x.danceability, 0) / t.length).toFixed(2);
  });

  avgValence = computed(() => {
    const t = this.tracks();
    return +(t.reduce((s, x) => s + x.valence, 0) / t.length).toFixed(2);
  });

  selectTrack(id: number) {
    this.selectedId.set(id);
  }

  featureValue(track: AudioFeatureTrack, key: keyof AudioFeatureTrack): number {
    const v = track[key];
    return typeof v === 'number' ? v : 0;
  }

  /** Punto individual del radar por índice de eje */
  radarPoint(track: AudioFeatureTrack, index: number): { x: number; y: number } {
    const cx = 100;
    const cy = 100;
    const maxR = 72;
    const key = this.featureDefs[index]?.key;
    if (!key) return { x: cx, y: cy };
    const n = this.featureDefs.length;
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
    const val = this.featureValue(track, key);
    const r = val * maxR;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  }

  /** Puntos SVG para radar chart (7 ejes, valor 0-1) */
  radarPoints(track: AudioFeatureTrack): string {
    return this.featureDefs
      .map((_, i) => {
        const p = this.radarPoint(track, i);
        return `${p.x},${p.y}`;
      })
      .join(' ');
  }

  radarAxisPoints(): { x: number; y: number; label: string; lx: number; ly: number }[] {
    const cx = 100;
    const cy = 100;
    const maxR = 72;
    const n = this.featureDefs.length;

    return this.featureDefs.map((f, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const x = cx + maxR * Math.cos(angle);
      const y = cy + maxR * Math.sin(angle);
      const lx = cx + (maxR + 18) * Math.cos(angle);
      const ly = cy + (maxR + 18) * Math.sin(angle);
      return { x, y, label: f.label, lx, ly };
    });
  }

  gridRings = [0.25, 0.5, 0.75, 1];
}
