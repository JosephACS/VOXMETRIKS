import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../shared/services/icon-render.service';
import { StatsService } from '../analytics/services/stats.service';
import { HistoryService } from '../streaming/services/history.service';
import { SearchHistoryService } from '../streaming/services/search-history.service';
import { MusicPlayerService } from '../../shared/services/music-player.service';
import { CoverArtService } from '../../shared/services/cover-art.service';
import { HistoryHub, HistoryEntry, SearchHistoryEntry } from '../../shared/models/api.models';
import { primaryArtistName } from '../../shared/utils/artist.util';

type HistoryTab = 'music' | 'user' | 'search';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css'],
})
export class HistoryComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  private stats = inject(StatsService);
  private localMusic = inject(HistoryService);
  private localSearch = inject(SearchHistoryService);
  private player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);

  activeTab = signal<HistoryTab>('music');
  isLoading = signal(true);
  hasError = signal(false);
  hub = signal<HistoryHub | null>(null);
  localMusicEntries = signal<HistoryEntry[]>([]);
  localSearchEntries = signal<SearchHistoryEntry[]>([]);

  warehouseSearches = computed(() => this.hub()?.search ?? []);
  userTimeline = computed(() => this.hub()?.user?.timeline ?? []);
  userFavorites = computed(() => this.hub()?.user?.favorites ?? []);

  musicCount = computed(() => this.localMusicEntries().length);
  userCount = computed(() => this.userTimeline().length);
  searchCount = computed(() => this.localSearchEntries().length + this.warehouseSearches().length);

  ngOnInit() {
    this.localMusic.history$.subscribe((h) => this.localMusicEntries.set(h));
    this.localMusic.reload();
    this.localSearch.history$.subscribe((h) => this.localSearchEntries.set(h));
    this.localSearch.reload();
    this.loadHub();
  }

  selectTab(tab: HistoryTab) {
    this.activeTab.set(tab);
  }

  loadHub() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.stats.getHistoryHub(30).subscribe({
      next: (d) => {
        this.hub.set(d);
        this.isLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.isLoading.set(false);
      },
    });
  }

  clearLocalMusic() {
    this.localMusic.clear();
  }

  clearLocalSearch() {
    this.localSearch.clear();
  }

  playFromHistory(item: HistoryEntry, e?: Event) {
    e?.stopPropagation();
    e?.preventDefault();
    const id = item.id_track;
    if (!id) return;
    this.player.playTrack({
      id,
      title: item.nombre_track,
      artist: this.artistName(item.nombre_artista),
      audioUrl: `/assets/audio/demo-${String((id % 8) + 1).padStart(2, '0')}.wav`,
      coverGradient: this.covers.gradientFor(id),
    });
  }

  artistName(raw?: string): string {
    return primaryArtistName(raw);
  }

  formatDate(iso?: string | null): string {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString('es', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  formatRelative(iso?: string | null): string {
    if (!iso) return '—';
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Ahora';
    if (mins < 60) return `Hace ${mins} min`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `Hace ${hrs} h`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `Hace ${days} d`;
    return this.formatDate(iso);
  }

  eventIcon(type?: string): string {
    const map: Record<string, string> = {
      login: 'log-in',
      favorite: 'heart',
      play: 'play',
      pause: 'pause',
      skip: 'skip-forward',
      like: 'heart',
      share: 'share',
      add_playlist: 'list',
    };
    return map[type ?? ''] ?? 'activity';
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
