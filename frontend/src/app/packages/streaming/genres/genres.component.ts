import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GenresService } from '../services/genres.service';
import { GeneroPopularidad } from '../../../shared/models/api.models';

type ModalMode = 'create' | 'edit' | 'delete' | null;

@Component({
  selector: 'app-genres',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './genres.component.html',
  styleUrls: ['./genres.component.css'],
})
export class GenresComponent implements OnInit {
  allGenres  = signal<GeneroPopularidad[]>([]);
  isLoading  = signal(true);
  hasError   = signal(false);
  errorMsg   = signal('');
  searchVal  = signal('');

  filteredGenres = computed(() => {
    const q = this.searchVal().toLowerCase().trim();
    if (!q) return this.allGenres();
    return this.allGenres().filter(g => (g.nombre_genero ?? '').toLowerCase().includes(q));
  });
  topGenre       = computed(() => this.allGenres()[0] ?? {});
  avgPopularity  = computed(() => { const g = this.allGenres(); if (!g.length) return null; const v = g.map(x => x.popularidad_promedio ?? 0).filter(v => v > 0); return v.length ? +(v.reduce((a,b)=>a+b,0)/v.length).toFixed(1) : null; });
  avgEnergy      = computed(() => { const g = this.allGenres(); if (!g.length) return null; const v = g.map(x => x.energia_promedio ?? 0).filter(v => v > 0); return v.length ? +(v.reduce((a,b)=>a+b,0)/v.length).toFixed(3) : null; });
  maxTracks      = computed(() => Math.max(...this.allGenres().map(g => g.total_tracks ?? 0), 1));

  modalMode  = signal<ModalMode>(null);
  modalGenre = signal<GeneroPopularidad | null>(null);
  formName   = signal('');
  formError  = signal('');
  formSaving = signal(false);

  constructor(private svc: GenresService) {}
  ngOnInit() { this.loadGenres(); }

  loadGenres() {
    this.isLoading.set(true); this.hasError.set(false);
    this.svc.getGenreStats(200).subscribe({
      next: d => { this.allGenres.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.errorMsg.set('Error al conectar con el backend. Verifica que FastAPI esté corriendo en http://localhost:8000'); this.isLoading.set(false); },
    });
  }

  onSearch(val: string) { this.searchVal.set(val); }
  clearSearch() { this.searchVal.set(''); }
  trackBar(tracks: number): number { return Math.round((tracks / this.maxTracks()) * 100); }
  skeletonRows = Array(10).fill(0);

  openCreate() { this.formName.set(''); this.formError.set(''); this.modalMode.set('create'); }
  openEdit(g: GeneroPopularidad) { this.modalGenre.set(g); this.formName.set(g.nombre_genero ?? ''); this.formError.set(''); this.modalMode.set('edit'); }
  openDelete(g: GeneroPopularidad) { this.modalGenre.set(g); this.formError.set(''); this.modalMode.set('delete'); }
  closeModal() { this.modalMode.set(null); this.formSaving.set(false); }

  saveCreate() {
    const name = this.formName().trim();
    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.createGenre({ nombre_genero: name }).subscribe({
      next: () => { this.closeModal(); this.loadGenres(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al crear género'); this.formSaving.set(false); },
    });
  }

  saveEdit() {
    const name = this.formName().trim(), genre = this.modalGenre();
    if (!name || !genre) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true); this.formError.set('');
    this.svc.updateGenre(genre.id_genero, { nombre_genero: name }).subscribe({
      next: () => { this.closeModal(); this.loadGenres(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al actualizar género'); this.formSaving.set(false); },
    });
  }

  confirmDelete() {
    const genre = this.modalGenre(); if (!genre) return;
    this.formSaving.set(true); this.formError.set('');
    this.svc.deleteGenre(genre.id_genero).subscribe({
      next: () => { this.closeModal(); this.loadGenres(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al eliminar género'); this.formSaving.set(false); },
    });
  }
}
