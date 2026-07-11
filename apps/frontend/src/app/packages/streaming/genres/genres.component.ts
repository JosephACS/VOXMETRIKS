import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { AuthService } from '../../../core/services/auth.service';
import { GenresService } from '../services/genres.service';
import { GeneroPopularidad } from '../../../shared/models/api.models';
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
  selector: 'app-genres',
  standalone: true,
  imports: [CommonModule, FormsModule, ScrollingModule, TranslatePipe, DataSourceBadgeComponent],
  templateUrl: './genres.component.html',
  styleUrls: [
    '../../../shared/styles/catalog-page-shared.css',
    '../../../shared/styles/catalog-crud-modal.css',
    './genres.component.css',
  ],
})
export class GenresComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private i18n = inject(I18nService);
  private iconRender = inject(IconRenderService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);
  protected readonly auth = inject(AuthService);

  genres     = signal<GeneroPopularidad[]>([]);
  isLoading  = signal(true);
  hasError   = signal(false);
  errorMsg   = signal('');
  page       = signal(1);
  limit      = 50;
  serverTotal = signal(0);
  searchVal  = signal('');
  private readonly searchDebouncer = createSearchDebouncer(this.destroyRef);

  totalPages   = computed(() => Math.max(1, Math.ceil(this.serverTotal() / this.limit)));
  displayTotal = computed(() => this.serverTotal());
  topGenre       = computed(() => this.genres()[0] ?? {});
  avgPopularity  = computed(() => { const g = this.genres(); if (!g.length) return null; const v = g.map(x => x.popularidad_promedio ?? 0).filter(v => v > 0); return v.length ? +(v.reduce((a,b)=>a+b,0)/v.length).toFixed(1) : null; });
  avgEnergy      = computed(() => { const g = this.genres(); if (!g.length) return null; const v = g.map(x => x.energia_promedio ?? 0).filter(v => v > 0); return v.length ? +(v.reduce((a,b)=>a+b,0)/v.length).toFixed(3) : null; });
  maxTracks      = computed(() => Math.max(...this.genres().map(g => g.total_tracks ?? 0), 1));

  modalMode  = signal<ModalMode>(null);
  modalGenre = signal<GeneroPopularidad | null>(null);
  formName   = signal('');
  formError  = signal('');
  formSaving = signal(false);

  constructor(private svc: GenresService) {}
  ngOnInit() {
    this.route.queryParamMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((pm) => {
        const q = pm.get('q') ?? pm.get('genre') ?? '';
        if (q !== this.searchVal()) this.searchVal.set(q);
        this.loadGenres();
      });
  }

  loadGenres() {
    this.isLoading.set(true); this.hasError.set(false);
    this.svc.getGenreStats(this.page(), this.limit, this.searchVal() || undefined).subscribe({
      next: (r) => {
        this.genres.set(r.items ?? []);
        this.serverTotal.set(r.total ?? 0);
        this.isLoading.set(false);
      },
      error: () => { this.hasError.set(true); this.errorMsg.set(this.i18n.t('errors.backendConnection')); this.isLoading.set(false); },
    });
  }

  onSearch(val: string) {
    this.searchDebouncer.schedule(() => { this.searchVal.set(val); this.page.set(1); this.loadGenres(); });
  }
  clearSearch() { this.searchVal.set(''); this.page.set(1); this.loadGenres(); }
  goTo(p: number) { if (p < 1 || p > this.totalPages()) return; this.page.set(p); this.loadGenres(); }
  get pageNumbers(): number[] { return pageWindow(this.page(), this.totalPages()); }
  rowIndex(i: number): number { return paginatedRowIndex(this.page(), this.limit, i); }
  trackGenre(_i: number, genre: GeneroPopularidad): number { return genre.id_genero; }
  trackBar(tracks: number): number { return Math.round((tracks / this.maxTracks()) * 100); }
  skeletonRows = Array(10).fill(0);

  /** Navigate to the catalog filtered by this genre's songs. */
  openGenreTracks(g: GeneroPopularidad) {
    if (g.id_genero == null) return;
    this.router.navigate(['/tracks'], {
      queryParams: { genre_id: g.id_genero, genre_name: g.nombre_genero ?? '' },
    });
  }

  openCreate() { if (!this.auth.isCatalogSteward()) return; this.formName.set(''); this.formError.set(''); this.modalMode.set('create'); }
  openEdit(g: GeneroPopularidad) { if (!this.auth.isCatalogSteward()) return; this.modalGenre.set(g); this.formName.set(g.nombre_genero ?? ''); this.formError.set(''); this.modalMode.set('edit'); }
  openDelete(g: GeneroPopularidad) { if (!this.auth.isCatalogSteward()) return; this.modalGenre.set(g); this.formError.set(''); this.modalMode.set('delete'); }
  closeModal() { this.modalMode.set(null); this.formSaving.set(false); }

  saveCreate() {
    if (!this.auth.isCatalogSteward()) return;
    const name = this.formName().trim();
    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.createGenre({ nombre_genero: name }).subscribe({
      next: () => { this.closeModal(); this.loadGenres(); },
      error: (e) => { this.formError.set(apiFormError(e, 'Error al crear género')); this.formSaving.set(false); },
    });
  }

  saveEdit() {
    if (!this.auth.isCatalogSteward()) return;
    const name = this.formName().trim(), genre = this.modalGenre();
    if (!name || !genre) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.updateGenre(genre.id_genero, { nombre_genero: name }).subscribe({
      next: () => { this.closeModal(); this.loadGenres(); },
      error: (e) => { this.formError.set(apiFormError(e, 'Error al actualizar género')); this.formSaving.set(false); },
    });
  }

  confirmDelete() {
    if (!this.auth.isCatalogSteward()) return;
    const genre = this.modalGenre(); if (!genre) return;
    this.formSaving.set(true); this.formError.set('');
    this.svc.deleteGenre(genre.id_genero).subscribe({
      next: () => { this.closeModal(); this.loadGenres(); },
      error: (e) => { this.formError.set(apiFormError(e, 'Error al eliminar género')); this.formSaving.set(false); },
    });
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
