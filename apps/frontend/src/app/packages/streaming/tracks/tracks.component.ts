import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
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
import { ScrollingModule } from '@angular/cdk/scrolling';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import {
  apiFormError,
  createSearchDebouncer,
  pageWindow,
  paginatedRowIndex,
} from '../../../shared/utils/catalog-list.util';

type ModalMode = 'create' | 'edit' | 'delete' | null;

@Component({
  selector: 'app-tracks',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, ScrollingModule, TrackRowComponent, TranslatePipe, DataSourceBadgeComponent],
  templateUrl: './tracks.component.html',
  styleUrls: [
    '../../../shared/styles/catalog-page-shared.css',
    '../../../shared/styles/catalog-crud-modal.css',
    './tracks.component.css',
  ],
})
export class TracksComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private i18n = inject(I18nService);
  private iconRender = inject(IconRenderService);
  protected readonly auth = inject(AuthService);
  player = inject(MusicPlayerService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);
  private readonly searchDebouncer = createSearchDebouncer(this.destroyRef);

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
    this.route.queryParamMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((pm) => {
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
      this.genresSvc.getGenres({ limit: 500 }).subscribe({
        next: r => this.genres.set(r.items ?? []),
        error: (err) => console.error('[TracksComponent] getGenres failed', err),
      });
      this.artistsSvc.listArtists(1, 500).subscribe({
        next: r => this.artists.set(r.items ?? []),
        error: (err) => console.error('[TracksComponent] listArtists failed', err),
      });
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
        this.errorMsg.set(this.i18n.t('errors.backendConnection'));
        this.isLoading.set(false);
      },
    });
  }

  onSearch(val: string) {
    this.searchDebouncer.schedule(() => { this.searchVal.set(val); this.page.set(1); this.loadTracks(); });
  }
  clearSearch() { this.searchVal.set(''); this.page.set(1); this.loadTracks(); }
  goTo(p: number) { if (p < 1 || p > this.totalPages()) return; this.page.set(p); this.loadTracks(); }
  get pageNumbers(): number[] { return pageWindow(this.page(), this.totalPages()); }
  rowIndex(i: number): number { return paginatedRowIndex(this.page(), this.limit, i); }
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
  trackById = (_: number, t: Track) => t.id_track;
  skeletonRows = Array(12).fill(0);

  openCreate() { if (!this.auth.isCatalogSteward()) return; this.formName.set(''); this.formArtist.set(null); this.formGenre.set(null); this.formExplicit.set(false); this.formDuration.set(null); this.formError.set(''); this.modalMode.set('create'); }
  openEdit(t: Track) { if (!this.auth.isCatalogSteward()) return; this.modalTrack.set(t); this.formName.set(t.nombre_track); this.formArtist.set(t.id_artista ?? null); this.formGenre.set(t.id_genero ?? null); this.formExplicit.set(t.explicit ?? false); this.formDuration.set(t.duration_ms ?? null); this.formError.set(''); this.modalMode.set('edit'); }
  openDelete(t: Track) { if (!this.auth.isCatalogSteward()) return; this.modalTrack.set(t); this.formError.set(''); this.modalMode.set('delete'); }
  closeModal() { this.modalMode.set(null); this.formSaving.set(false); }

  saveCreate() {
    if (!this.auth.isCatalogSteward()) return;
    const name = this.formName().trim();
    if (!name) { this.formError.set(this.i18n.t('form.nameRequired')); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.createTrack({ nombre_track: name, id_artista: this.formArtist() ?? undefined, id_genero: this.formGenre() ?? undefined, explicit: this.formExplicit(), duration_ms: this.formDuration() ?? undefined }).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(apiFormError(e, this.i18n.t('tracks.form.createError'))); this.formSaving.set(false); },
    });
  }

  saveEdit() {
    if (!this.auth.isCatalogSteward()) return;
    const name = this.formName().trim();
    const track = this.modalTrack();
    if (!name || !track) { this.formError.set(this.i18n.t('form.nameRequired')); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.updateTrack(track.id_track, { nombre_track: name, id_artista: this.formArtist() ?? undefined, id_genero: this.formGenre() ?? undefined, explicit: this.formExplicit(), duration_ms: this.formDuration() ?? undefined }).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(apiFormError(e, this.i18n.t('tracks.form.updateError'))); this.formSaving.set(false); },
    });
  }

  confirmDelete() {
    if (!this.auth.isCatalogSteward()) return;
    const track = this.modalTrack(); if (!track) return;
    this.formSaving.set(true); this.formError.set('');
    this.svc.deleteTrack(track.id_track).subscribe({
      next: () => { this.closeModal(); this.loadTracks(); },
      error: (e) => { this.formError.set(apiFormError(e, this.i18n.t('tracks.form.deleteError'))); this.formSaving.set(false); },
    });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
