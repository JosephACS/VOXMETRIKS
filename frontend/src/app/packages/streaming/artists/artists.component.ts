import { SafeHtml } from '@angular/platform-browser';

import { IconRenderService } from '../../../shared/services/icon-render.service';

import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { CommonModule } from '@angular/common';

import { FormsModule } from '@angular/forms';

import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { ScrollingModule } from '@angular/cdk/scrolling';

import { AuthService } from '../../../core/services/auth.service';

import { ArtistsService } from '../services/artists.service';

import { Artista, TopArtista, PaginatedResponse } from '../../../shared/models/api.models';

import { splitArtistNames, primaryArtistName } from '../../../shared/utils/artist.util';
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
  selector: 'app-artists',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, ScrollingModule, TranslatePipe, DataSourceBadgeComponent],

  templateUrl: './artists.component.html',

  styleUrls: [
    '../../../shared/styles/catalog-page-shared.css',
    '../../../shared/styles/catalog-crud-modal.css',
    './artists.component.css',
  ],

})

export class ArtistsComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private i18n = inject(I18nService);

  private iconRender = inject(IconRenderService);

  protected readonly auth = inject(AuthService);



  artists     = signal<Artista[]>([]);

  topArtists  = signal<TopArtista[]>([]);

  isLoading   = signal(true);

  hasError    = signal(false);

  errorMsg    = signal('');

  page        = signal(1);

  limit       = 50;

  serverTotal = signal(0);

  searchVal   = signal('');

  private destroyRef = inject(DestroyRef);
  private readonly searchDebouncer = createSearchDebouncer(this.destroyRef);



  totalPages   = computed(() => Math.max(1, Math.ceil(this.serverTotal() / this.limit)));

  displayTotal = computed(() => this.serverTotal());



  modalMode    = signal<ModalMode>(null);

  modalArtist  = signal<Artista | null>(null);

  formName     = signal('');

  formError    = signal('');

  formSaving   = signal(false);



  constructor(

    private svc: ArtistsService,

    private route: ActivatedRoute,

    private router: Router,

  ) {}



  ngOnInit() {

    this.loadTopArtists();

    this.route.queryParamMap

      .pipe(takeUntilDestroyed(this.destroyRef))

      .subscribe((pm) => {

      const q = pm.get('q') ?? '';

      if (q !== this.searchVal()) this.searchVal.set(q);

      this.loadArtists();

    });

  }



  artistNames(name: string): string[] {

    return splitArtistNames(name);

  }



  displayPrimaryName(name?: string | null): string {

    return primaryArtistName(name);

  }



  displayPrimaryInitial(name?: string | null): string {

    return primaryArtistName(name).charAt(0).toUpperCase() || '?';

  }



  loadTopArtists() {

    this.svc.getTopArtists(5).subscribe({
      next: d => this.topArtists.set(d),
      error: (err) => console.error('[ArtistsComponent] getTopArtists failed', err),
    });

  }



  loadArtists() {

    this.isLoading.set(true);

    this.hasError.set(false);

    this.svc.listArtists(this.page(), this.limit, this.searchVal() || undefined).subscribe({

      next: (res: PaginatedResponse<Artista>) => {

        this.artists.set(res.items ?? []);

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



  openArtist(id: number) {

    if (!id) return;

    this.router.navigate(['/artists', id]);

  }



  onSearch(val: string) {

    this.searchDebouncer.schedule(() => {

      this.searchVal.set(val);

      this.page.set(1);

      this.loadArtists();

    });

  }



  clearSearch() { this.searchVal.set(''); this.page.set(1); this.loadArtists(); }



  goTo(p: number) {

    if (p < 1 || p > this.totalPages()) return;

    this.page.set(p);

    this.loadArtists();

  }



  get pageNumbers(): number[] {

    return pageWindow(this.page(), this.totalPages());

  }



  rowIndex(i: number): number { return paginatedRowIndex(this.page(), this.limit, i); }

  trackArtist(_i: number, artist: Artista): number { return artist.id_artista; }

  skeletonRows = Array(12).fill(0);



  openCreate() {

    if (!this.auth.isCatalogSteward()) return;

    this.formName.set('');

    this.formError.set('');

    this.modalMode.set('create');

  }



  openEdit(a: Artista) {

    if (!this.auth.isCatalogSteward()) return;

    this.modalArtist.set(a);

    this.formName.set(a.nombre_artista);

    this.formError.set('');

    this.modalMode.set('edit');

  }



  openDelete(a: Artista) {

    if (!this.auth.isCatalogSteward()) return;

    this.modalArtist.set(a);

    this.formError.set('');

    this.modalMode.set('delete');

  }



  closeModal() {

    this.modalMode.set(null);

    this.formSaving.set(false);

  }



  saveCreate() {

    if (!this.auth.isCatalogSteward()) return;

    const name = this.formName().trim();

    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }

    this.formSaving.set(true);

    this.formError.set('');

    this.svc.createArtist({ nombre_artista: name }).subscribe({

      next: () => { this.closeModal(); this.loadArtists(); this.loadTopArtists(); },

      error: (e) => { this.formError.set(apiFormError(e, 'Error al crear artista')); this.formSaving.set(false); },

    });

  }



  saveEdit() {

    if (!this.auth.isCatalogSteward()) return;

    const name = this.formName().trim();

    const artist = this.modalArtist();

    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }

    if (!artist) return;

    this.formSaving.set(true);

    this.formError.set('');

    this.svc.updateArtist(artist.id_artista, { nombre_artista: name }).subscribe({

      next: () => { this.closeModal(); this.loadArtists(); this.loadTopArtists(); },

      error: (e) => { this.formError.set(apiFormError(e, 'Error al actualizar artista')); this.formSaving.set(false); },

    });

  }



  confirmDelete() {

    if (!this.auth.isCatalogSteward()) return;

    const artist = this.modalArtist();

    if (!artist) return;

    this.formSaving.set(true);

    this.formError.set('');

    this.svc.deleteArtist(artist.id_artista).subscribe({

      next: () => { this.closeModal(); this.loadArtists(); this.loadTopArtists(); },

      error: (e) => { this.formError.set(apiFormError(e, 'Error al eliminar artista')); this.formSaving.set(false); },

    });

  }



  icon(key: string, size = 18): SafeHtml {

    return this.iconRender.render(key, size);

  }

}

