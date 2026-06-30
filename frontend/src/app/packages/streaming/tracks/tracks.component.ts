import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { AuthService } from '../../../core/services/auth.service';
import { TracksService } from '../services/tracks.service';
import { GenresService } from '../services/genres.service';
import { ArtistsService } from '../services/artists.service';
import { Track, PaginatedResponse, Genero, Artista } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';

type ModalMode = 'create' | 'edit' | 'delete' | null;

@Component({
  selector: 'app-tracks',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TrackRowComponent, TranslatePipe, DataSourceBadgeComponent],
  templateUrl: './tracks.component.html',
  styleUrls: ['./tracks.component.css'],
})
export class TracksComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  protected readonly auth = inject(AuthService);
  player = inject(MusicPlayerService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

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
  genreFilterId   = signal<number | null>(null);
  genreFilterName = signal<string>('');
  artistFilterId   = signal<number | null>(null);
  artistFilterName = signal<string>('');
  private searchTimer: ReturnType<typeof setTimeout> | null = null;

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
    this.route.queryParamMap.subscribe((pm) => {
      const gid = pm.get('genre_id');
      const aid = pm.get('artist_id');
      this.genreFilterId.set(gid ? Number(gid) : null);
      this.genreFilterName.set(pm.get('genre_name') ?? '');
      this.artistFilterId.set(aid ? Number(aid) : null);
      this.artistFilterName.set(pm.get('artist_name') ?? '');
      this.page.set(1);
      this.loadTracks();
    });
    if (this.auth.isCatalogSteward()) {
      this.genresSvc.getGenres({ limit: 500 }).subscribe({ next: r => this.genres.set(r.items ?? []), error: () => {} });
      this.artistsSvc.listArtists(1, 500).subscribe({ next: r => this.artists.set(r.items ?? []), error: () => {} });
    }
  }

  hasActiveFilter = computed(() => this.genreFilterId() != null || this.artistFilterId() != null);

  clearFilters() {
    this.router.navigate(['/tracks']);
  }

  loadTracks() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.svc.listTracks(
      this.page(), this.limit,
      this.searchVal() || undefined,
      this.genreFilterId() ?? undefined,
      this.artistFilterId() ?? undefined,
    ).subscribe({
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
    if (this.searchTimer) clearTimeout(this.searchTimer);
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
  trackArtistName(t: Track): string {
    return primaryArtistName(t.nombre_artista) || (t.id_artista ? `#${t.id_artista}` : '—');
  }
  trackGenreName(t: Track): string {
    return t.nombre_genero?.trim() || (t.id_genero ? `#${t.id_genero}` : '');
  }
  trackQueue = computed(() => this.tracks().map((t) => this.player.fromTrack(t)));
  skeletonRows = Array(12).fill(0);

  openCreate() { if (!this.auth.isCatalogSteward()) return; this.formName.set(''); this.formArtist.set(null); this.formGenre.set(null); this.formExplicit.set(false); this.formDuration.set(null); this.formError.set(''); this.modalMode.set('create'); }
  openEdit(t: Track) { if (!this.auth.isCatalogSteward()) return; this.modalTrack.set(t); this.formName.set(t.nombre_track); this.formArtist.set(t.id_artista ?? null); this.formGenre.set(t.id_genero ?? null); this.formExplicit.set(t.explicit ?? false); this.formDuration.set(t.duration_ms ?? null); this.formError.set(''); this.modalMode.set('edit'); }
  openDelete(t: Track) { if (!this.auth.isCatalogSteward()) return; this.modalTrack.set(t); this.formError.set(''); this.modalMode.set('delete'); }
  closeModal() { this.modalMode.set(null); this.formSaving.set(false); }

  saveCreate() {
    if (!this.auth.isCatalogSteward()) return;
    const name = this.formName().trim();
    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.createTrack({ nombre_track: name, id_artista: this.formArtist() ?? undefined, id_genero: this.formGenre() ?? undefined, explicit: this.formExplicit(), duration_ms: this.formDuration() ?? undefined }).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al crear track'); this.formSaving.set(false); },
    });
  }

  saveEdit() {
    if (!this.auth.isCatalogSteward()) return;
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
    if (!this.auth.isCatalogSteward()) return;
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
