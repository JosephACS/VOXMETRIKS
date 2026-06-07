import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TracksService } from '../services/tracks.service';
import { ArtistsService } from '../services/artists.service';
import { TrackSearchResult, Artista } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { SearchHistoryService } from '../services/search-history.service';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, FavoriteBtnComponent],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css'],
})
export class SearchComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  query = signal('');
  trackResults = signal<TrackSearchResult[]>([]);
  artistResults = signal<Artista[]>([]);
  isLoading = signal(false);
  searched = signal(false);
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
      return;
    }
    this.isLoading.set(true);
    this.searched.set(true);
    const term = q.trim();
    let pending = 2;
    let trackCount = 0;
    let artistCount = 0;
    const done = () => {
      if (--pending <= 0) {
        this.isLoading.set(false);
        this.searchHistory.add(term, trackCount, artistCount);
      }
    };

    this.tracksSvc.searchTracks(term).subscribe({
      next: (d) => {
        const items = d ?? [];
        trackCount = items.length;
        this.trackResults.set(items);
        done();
      },
      error: () => { this.trackResults.set([]); done(); },
    });

    this.artistsSvc.listArtists(1, 20, term).subscribe({
      next: (res) => {
        const items = res.items ?? [];
        artistCount = items.length;
        this.artistResults.set(items);
        done();
      },
      error: () => { this.artistResults.set([]); done(); },
    });
  }

  hasResults(): boolean {
    return this.trackResults().length > 0 || this.artistResults().length > 0;
  }

  cover(i: number): string {
    const g = [
      'linear-gradient(135deg, #1ed896, #148f5e)',
      'linear-gradient(135deg, #3b82f6, #1e40af)',
      'linear-gradient(135deg, #10b981, #047857)',
    ];
    return g[i % g.length];
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  artistLabel(name?: string): string {
    return primaryArtistName(name);
  }
}
