import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MetricBarComponent } from '../../../shared/components/metric-bar/metric-bar.component';
import { TracksService } from '../services/tracks.service';
import { TrackDetail } from '../../../shared/models/api.models';

interface FeatureDef {
  key: keyof TrackDetail;
  label: string;
  color: string;
}

@Component({
  selector: 'app-audio-features',
  standalone: true,
  imports: [CommonModule, RouterModule, MetricBarComponent],
  templateUrl: './audio-features.component.html',
  styleUrls: ['./audio-features.component.css'],
})
export class AudioFeaturesComponent implements OnInit {
  private tracksSvc = inject(TracksService);

  featureDefs: FeatureDef[] = [
    { key: 'danceability', label: 'Bailabilidad', color: '#1ed896' },
    { key: 'energy', label: 'Energía', color: '#7c3aed' },
    { key: 'valence', label: 'Valencia', color: '#10b981' },
    { key: 'acousticness', label: 'Acústica', color: '#3b82f6' },
    { key: 'speechiness', label: 'Locución', color: '#f59e0b' },
    { key: 'instrumentalness', label: 'Instrumental', color: '#ec4899' },
    { key: 'liveness', label: 'En vivo', color: '#6366f1' },
  ];

  isLoading = signal(true);
  hasError = signal(false);
  tracks = signal<TrackDetail[]>([]);
  selectedId = signal(0);

  selectedTrack = computed((): TrackDetail | null =>
    this.tracks().find((t) => t.id_track === this.selectedId()) ?? this.tracks()[0] ?? null
  );

  selectedTrackTitle = computed(() => {
    const track = this.selectedTrack();
    return track?.nombre_track ?? '—';
  });

  avgEnergy = computed(() => {
    const t = this.tracks();
    if (!t.length) return 0;
    return +(t.reduce((s, x) => s + (x.energy ?? 0), 0) / t.length).toFixed(2);
  });

  avgDanceability = computed(() => {
    const t = this.tracks();
    if (!t.length) return 0;
    return +(t.reduce((s, x) => s + (x.danceability ?? 0), 0) / t.length).toFixed(2);
  });

  avgValence = computed(() => {
    const t = this.tracks();
    if (!t.length) return 0;
    return +(t.reduce((s, x) => s + (x.valence ?? 0), 0) / t.length).toFixed(2);
  });

  ngOnInit() {
    this.tracksSvc.listTracks(1, 8, undefined, undefined, undefined).subscribe({
      next: async (res) => {
        const items = res.items ?? [];
        const details: TrackDetail[] = [];
        for (const t of items.slice(0, 6)) {
          try {
            const d = await new Promise<TrackDetail>((resolve, reject) => {
              this.tracksSvc.getTrackDetail(t.id_track).subscribe({ next: resolve, error: reject });
            });
            details.push(d);
          } catch { /* skip */ }
        }
        this.tracks.set(details);
        if (details.length) this.selectedId.set(details[0].id_track);
        this.isLoading.set(false);
        if (!details.length) this.hasError.set(true);
      },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  selectTrack(id: number) {
    this.selectedId.set(id);
  }

  featureValue(track: TrackDetail, key: keyof TrackDetail): number {
    const v = track[key];
    return typeof v === 'number' ? v : 0;
  }

  radarPoint(track: TrackDetail, index: number): { x: number; y: number } {
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

  radarPoints(track: TrackDetail): string {
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
