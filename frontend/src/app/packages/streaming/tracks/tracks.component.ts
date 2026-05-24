import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { TracksService } from '../services/tracks.service';
import { GenresService } from '../services/genres.service';
import { ArtistsService } from '../services/artists.service';
import { Track, PaginatedResponse, Genero, Artista } from '../../../shared/models/api.models';

type ModalMode = 'create' | 'edit' | 'delete' | null;

@Component({
  selector: 'app-tracks',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, FavoriteBtnComponent],
  templateUrl: './tracks.component.html',
  styleUrls: ['./tracks.component.css'],
})
export class TracksComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  tracks      = signal<Track[]>([]);
  genres      = signal<Genero[]>([]);
  artists     = signal<Artista[]>([]);
  isLoading   = signal(true);
  hasError    = signal(false);
  errorMsg    = signal('');
  page        = signal(1);
  limit       = 50;
  serverTotal = signal(0);
  searchVal   = signal('');
  private searchTimer: any;

  totalPages   = computed(() => Math.max(1, Math.ceil(this.serverTotal() / this.limit)));
  displayTotal = computed(() => this.serverTotal());

  modalMode   = signal<ModalMode>(null);
  modalTrack  = signal<Track | null>(null);
  formName    = signal('');
  formArtist  = signal<number | null>(null);
  formGenre   = signal<number | null>(null);
  formExplicit = signal(false);
  formDuration = signal<number | null>(null);
  formError   = signal('');
  formSaving  = signal(false);

  constructor(private svc: TracksService, private genresSvc: GenresService, private artistsSvc: ArtistsService) {}

  ngOnInit() {
    this.loadTracks();
    this.genresSvc.getGenres({ limit: 200 }).subscribe({ next: r => this.genres.set(r.items ?? []), error: () => {} });
    this.artistsSvc.listArtists(1, 200).subscribe({ next: r => this.artists.set(r.items ?? []), error: () => {} });
  }

  loadTracks() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.svc.listTracks(this.page(), this.limit, this.searchVal() || undefined).subscribe({
      next: (res: PaginatedResponse<Track>) => {
        this.tracks.set(res.items ?? []);
        this.serverTotal.set(res.total ?? 0);
        this.isLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.errorMsg.set('Error al conectar con el backend. Verifica que FastAPI esté corriendo en http://localhost:8000');
        this.isLoading.set(false);
      },
    });
  }

  onSearch(val: string) {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => { this.searchVal.set(val); this.page.set(1); this.loadTracks(); }, 350);
  }
  clearSearch() { this.searchVal.set(''); this.page.set(1); this.loadTracks(); }
  goTo(p: number) { if (p < 1 || p > this.totalPages()) return; this.page.set(p); this.loadTracks(); }
  get pageNumbers(): number[] {
    const total = this.totalPages(), current = this.page(), delta = 2, range: number[] = [];
    for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) range.push(i);
    return range;
  }
  rowIndex(i: number): number { return (this.page() - 1) * this.limit + i + 1; }
  formatDuration(ms?: number): string {
    if (!ms) return '—';
    const m = Math.floor(ms / 60000), s = Math.floor((ms % 60000) / 1000);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }
  getArtistName(id?: number): string { return this.artists().find(a => a.id_artista === id)?.nombre_artista ?? (id ? `#${id}` : '—'); }
  getGenreName(id?: number): string { return this.genres().find(g => g.id_genero === id)?.nombre_genero ?? (id ? `#${id}` : '—'); }
  skeletonRows = Array(12).fill(0);

  openCreate() { this.formName.set(''); this.formArtist.set(null); this.formGenre.set(null); this.formExplicit.set(false); this.formDuration.set(null); this.formError.set(''); this.modalMode.set('create'); }
  openEdit(t: Track) { this.modalTrack.set(t); this.formName.set(t.nombre_track); this.formArtist.set(t.id_artista ?? null); this.formGenre.set(t.id_genero ?? null); this.formExplicit.set(t.explicit ?? false); this.formDuration.set(t.duration_ms ?? null); this.formError.set(''); this.modalMode.set('edit'); }
  openDelete(t: Track) { this.modalTrack.set(t); this.formError.set(''); this.modalMode.set('delete'); }
  closeModal() { this.modalMode.set(null); this.formSaving.set(false); }

  saveCreate() {
    const name = this.formName().trim();
    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.createTrack({ nombre_track: name, id_artista: this.formArtist() ?? undefined, id_genero: this.formGenre() ?? undefined, explicit: this.formExplicit(), duration_ms: this.formDuration() ?? undefined }).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al crear track'); this.formSaving.set(false); },
    });
  }

  saveEdit() {
    const name = this.formName().trim();
    const track = this.modalTrack();
    if (!name || !track) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.updateTrack(track.id_track, { nombre_track: name, id_artista: this.formArtist() ?? undefined, id_genero: this.formGenre() ?? undefined, explicit: this.formExplicit(), duration_ms: this.formDuration() ?? undefined }).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al actualizar'); this.formSaving.set(false); },
    });
  }

  confirmDelete() {
    const track = this.modalTrack(); if (!track) return;
    this.formSaving.set(true); this.formError.set('');
    this.svc.deleteTrack(track.id_track).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al eliminar'); this.formSaving.set(false); },
    });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
