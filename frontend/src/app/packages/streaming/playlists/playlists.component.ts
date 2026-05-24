import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { PlaylistsService } from '../services/playlists.service';
import { PlaylistSummary, PlaylistDetail, PlaylistTrackItem } from '../../../shared/models/api.models';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { PlayableTrack } from '../../../shared/models/player.models';

const COVERS = [
  'linear-gradient(135deg, #1ed896, #148f5e)',
  'linear-gradient(135deg, #3b82f6, #1e40af)',
  'linear-gradient(135deg, #10b981, #047857)',
  'linear-gradient(135deg, #ec4899, #9d174d)',
  'linear-gradient(135deg, #f59e0b, #b45309)',
  'linear-gradient(135deg, #6366f1, #312e81)',
];

@Component({
  selector: 'app-playlists',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TrackRowComponent],
  templateUrl: './playlists.component.html',
  styleUrls: ['./playlists.component.css'],
})
export class PlaylistsComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  private player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);

  playlists = signal<PlaylistSummary[]>([]);
  selected = signal<PlaylistDetail | null>(null);
  isLoading = signal(true);
  showCreate = signal(false);
  showDetail = signal(false);
  formName = signal('');
  formDesc = signal('');
  formError = signal('');
  saving = signal(false);

  constructor(private svc: PlaylistsService) {}

  ngOnInit() {
    this.load();
  }

  load() {
    this.isLoading.set(true);
    this.svc.list().subscribe({
      next: (d) => { this.playlists.set(d ?? []); this.isLoading.set(false); },
      error: () => this.isLoading.set(false),
    });
  }

  cover(i: number): string {
    return COVERS[i % COVERS.length];
  }

  detailGradient(): string {
    const det = this.selected();
    return det ? this.covers.gradientFor('pl-' + det.id) : COVERS[0];
  }

  playlistQueue(tracks: PlaylistTrackItem[]): PlayableTrack[] {
    return tracks.map((t) => ({
      id: t.id_track,
      title: t.nombre_track ?? '—',
      artist: t.nombre_artista ?? '—',
      audioUrl: `/assets/audio/demo-${String((t.id_track % 8) + 1).padStart(2, '0')}.wav`,
      coverGradient: this.covers.gradientFor(t.id_track),
    }));
  }

  playPlaylist() {
    const det = this.selected();
    if (!det?.tracks.length) return;
    const queue = this.playlistQueue(det.tracks);
    this.player.setQueue(queue, 0);
  }

  mockDuration(tracks: number): string {
    const mins = Math.round(tracks * 3.5);
    return mins >= 60 ? `${Math.floor(mins / 60)}h ${mins % 60}m` : `${mins} min`;
  }

  openCreate() {
    this.formName.set('');
    this.formDesc.set('');
    this.formError.set('');
    this.showCreate.set(true);
  }

  closeCreate() {
    this.showCreate.set(false);
    this.saving.set(false);
  }

  saveCreate() {
    const name = this.formName().trim();
    if (!name) { this.formError.set('Nombre requerido'); return; }
    this.saving.set(true);
    this.svc.create({ name, description: this.formDesc().trim() || undefined }).subscribe({
      next: () => { this.closeCreate(); this.load(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al crear'); this.saving.set(false); },
    });
  }

  openDetail(pl: PlaylistSummary) {
    this.svc.get(pl.id).subscribe({
      next: (d) => { this.selected.set(d); this.showDetail.set(true); },
    });
  }

  closeDetail() {
    this.showDetail.set(false);
    this.selected.set(null);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
