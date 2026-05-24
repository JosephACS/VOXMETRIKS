import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ArtistsService } from '../../services/artists.service';
import { Artista, TopArtista, PaginatedResponse } from '../../shared/models/api.models';

type ModalMode = 'create' | 'edit' | 'delete' | null;

@Component({
  selector: 'app-artists',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './artists.component.html',
  styleUrls: ['./artists.component.css'],
})
export class ArtistsComponent implements OnInit {
  artists     = signal<Artista[]>([]);
  topArtists  = signal<TopArtista[]>([]);
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

  // CRUD Modal state
  modalMode    = signal<ModalMode>(null);
  modalArtist  = signal<Artista | null>(null);
  formName     = signal('');
  formError    = signal('');
  formSaving   = signal(false);

  constructor(private svc: ArtistsService) {}

  ngOnInit() {
    this.loadTopArtists();
    this.loadArtists();
  }

  loadTopArtists() {
    this.svc.getTopArtists(5).subscribe({ next: d => this.topArtists.set(d), error: () => {} });
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
        this.errorMsg.set('Error al conectar con el backend. Verifica que FastAPI esté corriendo en http://localhost:8000');
        this.isLoading.set(false);
      },
    });
  }

  onSearch(val: string) {
    clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => {
      this.searchVal.set(val);
      this.page.set(1);
      this.loadArtists();
    }, 350);
  }

  clearSearch() { this.searchVal.set(''); this.page.set(1); this.loadArtists(); }

  goTo(p: number) {
    if (p < 1 || p > this.totalPages()) return;
    this.page.set(p);
    this.loadArtists();
  }

  get pageNumbers(): number[] {
    const total = this.totalPages(), current = this.page(), delta = 2;
    const range: number[] = [];
    for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) range.push(i);
    return range;
  }

  rowIndex(i: number): number { return (this.page() - 1) * this.limit + i + 1; }
  skeletonRows = Array(12).fill(0);

  // ── CRUD ──────────────────────────────────────────────────────────────────

  openCreate() {
    this.formName.set('');
    this.formError.set('');
    this.modalMode.set('create');
  }

  openEdit(a: Artista) {
    this.modalArtist.set(a);
    this.formName.set(a.nombre_artista);
    this.formError.set('');
    this.modalMode.set('edit');
  }

  openDelete(a: Artista) {
    this.modalArtist.set(a);
    this.formError.set('');
    this.modalMode.set('delete');
  }

  closeModal() {
    this.modalMode.set(null);
    this.formSaving.set(false);
  }

  saveCreate() {
    const name = this.formName().trim();
    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }
    this.formSaving.set(true);
    this.formError.set('');
    this.svc.createArtist({ nombre_artista: name }).subscribe({
      next: () => { this.closeModal(); this.loadArtists(); this.loadTopArtists(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al crear artista'); this.formSaving.set(false); },
    });
  }

  saveEdit() {
    const name = this.formName().trim();
    const artist = this.modalArtist();
    if (!name) { this.formError.set('El nombre no puede estar vacío'); return; }
    if (!artist) return;
    this.formSaving.set(true);
    this.formError.set('');
    this.svc.updateArtist(artist.id_artista, { nombre_artista: name }).subscribe({
      next: () => { this.closeModal(); this.loadArtists(); this.loadTopArtists(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al actualizar artista'); this.formSaving.set(false); },
    });
  }

  confirmDelete() {
    const artist = this.modalArtist();
    if (!artist) return;
    this.formSaving.set(true);
    this.formError.set('');
    this.svc.deleteArtist(artist.id_artista).subscribe({
      next: () => { this.closeModal(); this.loadArtists(); this.loadTopArtists(); },
      error: (e) => { this.formError.set(e?.error?.detail ?? 'Error al eliminar artista'); this.formSaving.set(false); },
    });
  }
}
