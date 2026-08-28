import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MetricBarComponent } from '../../../shared/components/metric-bar/metric-bar.component';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { I18nService } from '../../../core/services/i18n.service';
import { TracksService } from '../services/tracks.service';
import { TrackDetail } from '../../../shared/models/api.models';
import { TranslationKey } from '../../../core/i18n/translations';

interface FeatureDef {
  key: keyof TrackDetail;
  labelKey: TranslationKey;
  helpKey: TranslationKey;
  color: string;
}

@Component({
  selector: 'app-audio-features',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MetricBarComponent,
    DataSourceBadgeComponent, EmptyStateComponent, TranslatePipe,
  ],
  templateUrl: './audio-features.component.html',
  styleUrls: ['./audio-features.component.css'],
})
export class AudioFeaturesComponent implements OnInit {
  private tracksSvc = inject(TracksService);
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  readonly featureDefs: FeatureDef[] = [
    { key: 'danceability', labelKey: 'audioFeatures.feature.danceability', helpKey: 'audioFeatures.help.danceability', color: '#e8a33d' },
    { key: 'energy', labelKey: 'audioFeatures.feature.energy', helpKey: 'audioFeatures.help.energy', color: '#e8a33d' },
    { key: 'valence', labelKey: 'audioFeatures.feature.valence', helpKey: 'audioFeatures.help.valence', color: '#10b981' },
    { key: 'acousticness', labelKey: 'audioFeatures.feature.acousticness', helpKey: 'audioFeatures.help.acousticness', color: '#3b82f6' },
    { key: 'speechiness', labelKey: 'audioFeatures.feature.speechiness', helpKey: 'audioFeatures.help.speechiness', color: '#f59e0b' },
    { key: 'instrumentalness', labelKey: 'audioFeatures.feature.instrumentalness', helpKey: 'audioFeatures.help.instrumentalness', color: '#ec4899' },
    { key: 'liveness', labelKey: 'audioFeatures.feature.liveness', helpKey: 'audioFeatures.help.liveness', color: '#e8a33d' },
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
    this.loadFeatures();
  }

  featureLabel(def: FeatureDef): string {
    return this.i18n.t(def.labelKey);
  }

  featureHelp(def: FeatureDef): string {
    return this.i18n.t(def.helpKey);
  }

  loadFeatures() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.tracks.set([]);
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

  featurePct(track: TrackDetail, key: keyof TrackDetail): number {
    return Math.max(0, Math.min(100, this.featureValue(track, key) * 100));
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
      return { x, y, label: this.featureLabel(f), lx, ly };
    });
  }

  gridRings = [0.25, 0.5, 0.75, 1];
}
