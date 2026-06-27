import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TracksService } from '../services/tracks.service';
import { ArtistsService } from '../services/artists.service';
import { TrackSearchResult, Artista } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { SearchHistoryService } from '../services/search-history.service';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, FavoriteBtnComponent, DataSourceBadgeComponent, TranslatePipe],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css'],
})
export class SearchComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  private covers = inject(CoverArtService);

  query = signal('');
  trackResults = signal<TrackSearchResult[]>([]);
  artistResults = signal<Artista[]>([]);
  isLoading = signal(false);
  searched = signal(false);
  hasError = signal(false);
  errorMessage = signal('');
  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private route: ActivatedRoute,
    private tracksSvc: TracksService,
    private artistsSvc: ArtistsService,
    private searchHistory: SearchHistoryService,
  ) {}

  ngOnInit() {
    this.route.queryParamMap.subscribe((pm) => {
      const q = pm.get('q') ?? '';
      this.query.set(q);
      if (q.trim()) this.runSearch(q);
    });
  }

  onInput(val: string) {
    this.query.set(val);
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => this.runSearch(val), 350);
  }

  runSearch(q: string) {
    if (!q.trim()) {
      this.trackResults.set([]);
      this.artistResults.set([]);
      this.searched.set(false);
      this.hasError.set(false);
      this.errorMessage.set('');
      return;
    }
    this.isLoading.set(true);
    this.searched.set(true);
    this.hasError.set(false);
    this.errorMessage.set('');
    const term = q.trim();
    let pending = 2;
    let trackCount = 0;
    let artistCount = 0;
    let failed = 0;
    const done = () => {
      if (--pending <= 0) {
        this.isLoading.set(false);
        if (failed > 0) {
          this.hasError.set(true);
          this.errorMessage.set(
            failed === 2
              ? 'No se pudo consultar el catálogo. Verifica que el backend esté activo.'
              : 'Algunos resultados no se pudieron cargar. Intenta nuevamente.',
          );
        } else {
          this.searchHistory.add(term, trackCount, artistCount);
        }
      }
    };

    this.tracksSvc.searchTracks(term, 100).subscribe({
      next: (d) => {
        const items = d ?? [];
        trackCount = items.length;
        this.trackResults.set(items);
        done();
      },
      error: () => { failed += 1; this.trackResults.set([]); done(); },
    });

    this.artistsSvc.listArtists(1, 20, term).subscribe({
      next: (res) => {
        const items = res.items ?? [];
        artistCount = items.length;
        this.artistResults.set(items);
        done();
      },
      error: () => { failed += 1; this.artistResults.set([]); done(); },
    });
  }

  retrySearch() {
    this.runSearch(this.query());
  }

  hasResults(): boolean {
    return this.trackResults().length > 0 || this.artistResults().length > 0;
  }

  cover(trackId: number): string {
    return this.covers.gradientFor(trackId);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  artistLabel(name?: string): string {
    return primaryArtistName(name);
  }

  displayTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }
}
