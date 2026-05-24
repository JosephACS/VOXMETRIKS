import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TracksService } from '../services/tracks.service';
import { TrackSearchResult } from '../../../shared/models/api.models';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';

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
  results = signal<TrackSearchResult[]>([]);
  isLoading = signal(false);
  searched = signal(false);
  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor(private route: ActivatedRoute, private tracksSvc: TracksService) {}

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
      this.results.set([]);
      this.searched.set(false);
      return;
    }
    this.isLoading.set(true);
    this.searched.set(true);
    this.tracksSvc.searchTracks(q.trim()).subscribe({
      next: (d) => { this.results.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.results.set([]); this.isLoading.set(false); },
    });
  }

  cover(i: number): string {
    const g = [
      'linear-gradient(135deg, #ff8c42, #7c3aed)',
      'linear-gradient(135deg, #3b82f6, #1e40af)',
      'linear-gradient(135deg, #10b981, #047857)',
    ];
    return g[i % g.length];
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
