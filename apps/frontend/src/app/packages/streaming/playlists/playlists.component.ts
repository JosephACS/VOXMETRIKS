import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { PlaylistsService } from '../services/playlists.service';
import { PlaylistSummary, PlaylistDetail, PlaylistTrackItem } from '../../../shared/models/api.models';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { CoverMosaicComponent } from '../../../shared/components/cover-mosaic/cover-mosaic.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { PlayableTrack } from '../../../shared/models/player.models';
import { apiFormError } from '../../../shared/utils/catalog-list.util';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';

type PlaylistTab = 'mine' | 'catalog';

@Component({
  selector: 'app-playlists',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    TrackRowComponent,
    CoverMosaicComponent,
    TranslatePipe,
    DataSourceBadgeComponent,
  ],
  templateUrl: './playlists.component.html',
  styleUrls: [
    '../../../shared/styles/catalog-page-shared.css',
    './playlists.component.css',
  ],
})
export class PlaylistsComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private i18n = inject(I18nService);
  private confirm = inject(ConfirmDialogService);
  private iconRender = inject(IconRenderService);
  private readonly controller = inject(PlayerController);
  private covers = inject(CoverArtService);
  private destroyRef = inject(DestroyRef);

  playlists = signal<PlaylistSummary[]>([]);
  catalogPlaylists = signal<PlaylistSummary[]>([]);
  catalogTotal = signal(0);
  catalogPage = signal(1);
  catalogSearch = signal('');
  tab = signal<PlaylistTab>('mine');
  selected = signal<PlaylistDetail | null>(null);
  detailId = signal<number | null>(null);
  isCatalogDetail = signal(false);
  isLoading = signal(true);
  catalogLoading = signal(false);
  detailLoading = signal(false);
  hasError = signal(false);
  catalogError = signal(false);
  detailError = signal(false);
  showCreate = signal(false);
  showEdit = signal(false);
  formName = signal('');
  formDesc = signal('');
  formError = signal('');
  saving = signal(false);
  editingId = signal<number | null>(null);

  private catalogSearch$ = new Subject<string>();

  constructor(
    private svc: PlaylistsService,
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  ngOnInit() {
    this.catalogSearch$
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe((q) => {
        this.catalogSearch.set(q);
        this.catalogPage.set(1);
        this.loadCatalog();
      });

    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((pm) => {
        const raw = pm.get('id');
        const path = this.route.snapshot.routeConfig?.path ?? '';
        const catalog = path.includes('catalog');
        this.isCatalogDetail.set(catalog);
        if (raw) {
          this.detailId.set(Number(raw));
          this.openDetailById(Number(raw), catalog);
        } else {
          this.detailId.set(null);
          this.selected.set(null);
          this.detailError.set(false);
          this.syncTabFromQuery();
          this.load();
          if (this.tab() === 'catalog') this.loadCatalog();
        }
      });

    this.route.queryParamMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        if (this.detailId()) return;
        const prev = this.tab();
        this.syncTabFromQuery();
        if (this.tab() === 'catalog' && (prev !== 'catalog' || !this.catalogPlaylists().length)) {
          this.loadCatalog();
        }
      });
  }

  private syncTabFromQuery(): void {
    const t = this.route.snapshot.queryParamMap.get('tab');
    this.tab.set(t === 'catalog' ? 'catalog' : 'mine');
  }

  setTab(next: PlaylistTab): void {
    this.tab.set(next);
    void this.router.navigate(['/playlists'], {
      queryParams: next === 'catalog' ? { tab: 'catalog' } : {},
    });
    if (next === 'catalog') this.loadCatalog();
  }

  load() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.svc.list().subscribe({
      next: (d) => { this.playlists.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  loadCatalog(page = this.catalogPage()): void {
    this.catalogLoading.set(true);
    this.catalogError.set(false);
    this.catalogPage.set(page);
    this.svc.listCatalog({
      page,
      limit: 24,
      search: this.catalogSearch() || undefined,
    }).subscribe({
      next: (res) => {
        this.catalogPlaylists.set(res.items ?? []);
        this.catalogTotal.set(res.total ?? 0);
        this.catalogLoading.set(false);
      },
      error: () => {
        this.catalogError.set(true);
        this.catalogLoading.set(false);
      },
    });
  }

  onCatalogSearch(value: string): void {
    this.catalogSearch$.next(value);
  }

  catalogTotalPages(): number {
    return Math.max(1, Math.ceil(this.catalogTotal() / 24));
  }

  previewIds(pl: PlaylistSummary | PlaylistDetail): number[] {
    if (pl.preview_track_ids?.length) return pl.preview_track_ids.slice(0, 4);
    if ('tracks' in pl && Array.isArray(pl.tracks)) {
      return pl.tracks.slice(0, 4).map((t) => t.id_track);
    }
    if (pl.cover_track_id) return [pl.cover_track_id];
    return [];
  }

  detailGradient(): string {
    const det = this.selected();
    return det ? this.covers.gradientFor('pl-' + det.id) : this.covers.gradientFor('playlist');
  }

  playlistQueue(tracks: PlaylistTrackItem[]): PlayableTrack[] {
    return tracks.map((t) => ({
      id: t.id_track,
      title: t.nombre_track ?? '—',
      artist: t.nombre_artista ?? '—',
      artistId: t.id_artista,
      durationMs: t.duration_ms,
      audioUrl: '',
      coverGradient: this.covers.gradientFor(t.id_track),
    }));
  }

  playPlaylist() {
    const det = this.selected();
    if (!det?.tracks.length) return;
    const queue = this.playlistQueue(det.tracks);
    this.controller.setQueue(queue, 0);
  }

  formatDuration(tracks: PlaylistTrackItem[]): string {
    const ms = tracks.reduce((s, t) => s + (t.duration_ms ?? 210000), 0);
    const mins = Math.round(ms / 60000);
    if (!mins) return '0 min';
    return mins >= 60 ? `${Math.floor(mins / 60)}h ${mins % 60}m` : `${mins} min`;
  }

  durationLabel(count: number, tracks?: PlaylistTrackItem[]): string {
    if (tracks?.length) return this.formatDuration(tracks);
    const mins = Math.round(count * 3.5);
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
      error: (e) => { this.formError.set(apiFormError(e, 'Error al crear')); this.saving.set(false); },
    });
  }

  openDetail(pl: PlaylistSummary, catalog = false) {
    if (catalog || pl.source === 'catalog') {
      this.router.navigate(['/playlists/catalog', pl.id]);
    } else {
      this.router.navigate(['/playlists', pl.id]);
    }
  }

  openDetailById(id: number, catalog = false) {
    if (!Number.isFinite(id) || id <= 0) {
      this.router.navigate(['/playlists']);
      return;
    }
    this.detailLoading.set(true);
    this.detailError.set(false);
    this.selected.set(null);
    const req = catalog ? this.svc.getCatalog(id) : this.svc.get(id);
    req.subscribe({
      next: (d) => {
        this.selected.set({ ...d, source: catalog ? 'catalog' : d.source });
        this.detailLoading.set(false);
      },
      error: () => {
        this.detailLoading.set(false);
        this.detailError.set(true);
        this.selected.set(null);
      },
    });
  }

  backToList() {
    this.router.navigate(['/playlists'], {
      queryParams: this.isCatalogDetail() ? { tab: 'catalog' } : {},
    });
  }

  openEdit(det: PlaylistDetail) {
    if (det.source === 'catalog' || this.isCatalogDetail()) return;
    this.editingId.set(det.id);
    this.formName.set(det.name);
    this.formDesc.set(det.description ?? '');
    this.formError.set('');
    this.showEdit.set(true);
  }

  closeEdit() {
    this.showEdit.set(false);
    this.editingId.set(null);
    this.saving.set(false);
  }

  saveEdit() {
    const id = this.editingId();
    const name = this.formName().trim();
    if (!id || !name) { this.formError.set('Nombre requerido'); return; }
    this.saving.set(true);
    this.svc.update(id, { name, description: this.formDesc().trim() || undefined }).subscribe({
      next: (updated) => {
        this.closeEdit();
        this.load();
        const det = this.selected();
        if (det?.id === id) {
          this.selected.set({ ...det, name: updated.name, description: updated.description });
        }
      },
      error: (e) => { this.formError.set(apiFormError(e, 'Error al guardar')); this.saving.set(false); },
    });
  }

  deletePlaylist(det: PlaylistDetail) {
    if (det.source === 'catalog' || this.isCatalogDetail()) return;
    void this.confirm.open({
      title: this.i18n.t('confirm.deleteTitle'),
      message: `${this.i18n.t('playlists.deleteConfirm', { name: det.name })}\n\n${this.i18n.t('playlists.deleteWarn')}`,
      confirmLabel: this.i18n.t('common.delete'),
      cancelLabel: this.i18n.t('common.cancel'),
      danger: true,
    }).then((ok) => {
      if (!ok) return;
      this.svc.delete(det.id).subscribe({
        next: () => { this.backToList(); },
      });
    });
  }

  removeTrack(trackId: number) {
    const det = this.selected();
    if (!det || det.source === 'catalog' || this.isCatalogDetail()) return;
    this.svc.removeTrack(det.id, trackId).subscribe({
      next: () => {
        this.svc.get(det.id).subscribe({
          next: (d) => { this.selected.set(d); this.load(); },
        });
      },
    });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
