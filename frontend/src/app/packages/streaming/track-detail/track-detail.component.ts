import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { TracksService } from '../services/tracks.service';
import { HistoryService } from '../services/history.service';
import { TrackDetail } from '../../../shared/models/api.models';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { AddToPlaylistBtnComponent } from '../../../shared/components/add-to-playlist-btn/add-to-playlist-btn.component';

@Component({
  selector: 'app-track-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent, AddToPlaylistBtnComponent],
  templateUrl: './track-detail.component.html',
  styleUrls: ['./track-detail.component.css'],
})
export class TrackDetailComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  track = signal<TrackDetail | null>(null);
  isLoading = signal(true);
  hasError = signal(false);

  featureBars = computed(() => {
    const t = this.track();
    if (!t) return [];
    return [
      { label: 'Energía', value: (t.energy ?? 0) * 100, color: '#1ed896' },
      { label: 'Bailabilidad', value: (t.danceability ?? 0) * 100, color: '#7c3aed' },
      { label: 'Valencia', value: (t.valence ?? 0) * 100, color: '#10b981' },
      { label: 'Acústica', value: (t.acousticness ?? 0) * 100, color: '#3b82f6' },
    ];
  });

  sparkPoints = computed(() => {
    const t = this.track();
    if (!t) return '';
    const vals = [
      (t.energy ?? 0) * 80,
      (t.danceability ?? 0) * 70,
      (t.valence ?? 0) * 90,
      (t.acousticness ?? 0) * 60,
      (t.speechiness ?? 0) * 50,
      (t.instrumentalness ?? 0) * 40,
      (t.liveness ?? 0) * 55,
    ];
    return vals.map((v, i) => `${i * 40 + 10},${90 - v}`).join(' ');
  });

  constructor(
    private route: ActivatedRoute,
    private tracksSvc: TracksService,
    private history: HistoryService,
  ) {}

  ngOnInit() {
    this.route.paramMap.subscribe((pm) => {
      const id = Number(pm.get('id'));
      if (!id) return;
      this.load(id);
    });
  }

  load(id: number) {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.tracksSvc.getTrackDetail(id).subscribe({
      next: (d) => {
        this.track.set(d);
        this.isLoading.set(false);
        this.history.add({
          id_track: d.id_track,
          nombre_track: d.nombre_track ?? 'Track',
          nombre_artista: d.nombre_artista,
        });
      },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  formatDuration(ms?: number): string {
    if (!ms) return '—';
    const m = Math.floor(ms / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  coverGradient(): string {
    const t = this.track();
    const seed = t?.id_track ?? 0;
    const hues = ['#1ed896', '#7c3aed', '#3b82f6', '#10b981'];
    return `linear-gradient(135deg, ${hues[seed % hues.length]}, ${hues[(seed + 1) % hues.length]})`;
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
