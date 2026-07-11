import { I18nService } from '../../core/services/i18n.service';
import { Component, inject, OnInit, signal, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../shared/services/icon-render.service';
import { StatsService } from '../analytics/services/stats.service';
import { HistoryService } from '../streaming/services/history.service';
import { SearchHistoryService } from '../streaming/services/search-history.service';
import { TrackActionsComponent } from '../../shared/components/track-actions/track-actions.component';
import { PlayerController } from '../../playback-core/player.controller';
import { toPlayableFromHistory } from '../../playback-core/adapters/track.adapter';
import { CoverArtService } from '../../shared/services/cover-art.service';
import { HistoryHub, HistoryEntry, SearchHistoryEntry } from '../../shared/models/api.models';
import { primaryArtistName } from '../../shared/utils/artist.util';
import { displayTrackTitle } from '../../shared/utils/track-display.util';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../shared/components/data-source-badge/data-source-badge.component';

type HistoryTab = 'music' | 'user' | 'search';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, DataSourceBadgeComponent, TrackActionsComponent],
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css'],
})
export class HistoryComponent implements OnInit, OnDestroy {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private tabSub?: Subscription;
  private stats = inject(StatsService);
  private localMusic = inject(HistoryService);
  private localSearch = inject(SearchHistoryService);
  private readonly controller = inject(PlayerController);
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
    this.tabSub = this.route.queryParamMap.subscribe((params) => {
      const tab = params.get('tab');
      if (tab === 'user' || tab === 'search' || tab === 'music') {
        this.activeTab.set(tab);
      }
    });
    this.localMusic.history$.subscribe((h) => this.localMusicEntries.set(h));
    this.localMusic.reload();
    this.localSearch.history$.subscribe((h) => this.localSearchEntries.set(h));
    this.localSearch.reload();
    this.loadHub();
  }

  selectTab(tab: HistoryTab) {
    this.activeTab.set(tab);
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  ngOnDestroy() {
    this.tabSub?.unsubscribe();
  }

  loadHub() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.stats.getHistoryHub(30).subscribe({
      next: (d) => {
        this.hub.set(d);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.hasError.set(true);
        this.isLoading.set(false);
        console.error('[HistoryComponent] getHistoryHub failed', err);
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
    this.controller.playTrack(toPlayableFromHistory(this.covers, item));
  }

  historyPlayable(item: HistoryEntry) {
    return toPlayableFromHistory(this.covers, item);
  }

  historyQueue = computed(() =>
    this.localMusicEntries().map((h) => toPlayableFromHistory(this.covers, h)),
  );

  artistName(raw?: string): string {
    return primaryArtistName(raw);
  }

  trackTitle(raw?: string | null): string {
    return displayTrackTitle(raw);
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
      login: 'user',
      favorite: 'heart',
      play: 'play',
      pause: 'music',
      skip: 'music',
      like: 'heart',
      share: 'link',
      add_playlist: 'playlist',
    };
    return map[type ?? ''] ?? 'activity';
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
