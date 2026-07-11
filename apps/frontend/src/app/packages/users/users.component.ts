import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { KpiCardComponent } from '../../shared/components/kpi-card/kpi-card.component';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../shared/components/data-source-badge/data-source-badge.component';
import { UserService } from './services/user.service';
import { HistoryService } from '../streaming/services/history.service';
import { StatsService } from '../analytics/services/stats.service';
import { UiPreferencesService } from '../../core/services/ui-preferences.service';
import { I18nService } from '../../core/services/i18n.service';
import { UserProfile, HistoryEntry } from '../../shared/models/api.models';

interface ListenRecord {
  id: number;
  track: string;
  artist: string;
  genre: string;
  duration: string;
  playedAt: string;
}

interface TopItem {
  name: string;
  value: number;
  color: string;
}

interface ActivityItem {
  id: number;
  type: string;
  title: string;
  detail: string;
  time: string;
  iconKey: string;
}

interface PlaylistCard {
  id: number;
  name: string;
  tracks: number;
  gradient: string;
}

interface RecentItem extends ListenRecord {
  coverGradient: string;
}

const COVER_GRADIENTS = [
  'linear-gradient(135deg, #1ed896 0%, #7c3aed 100%)',
  'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
  'linear-gradient(135deg, #10b981 0%, #047857 100%)',
  'linear-gradient(135deg, #ec4899 0%, #9d174d 100%)',
  'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
  'linear-gradient(135deg, #6366f1 0%, #312e81 100%)',
  'linear-gradient(135deg, #ef4444 0%, #991b1b 100%)',
  'linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)',
];

const AUDIO_LABELS: Record<string, string> = {
  high: 'Alta (320 kbps)',
  normal: 'Normal (160 kbps)',
  low: 'Baja (96 kbps)',
};

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, KpiCardComponent, TranslatePipe, DataSourceBadgeComponent],
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css'],
})
export class UsersComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);

  private userSvc = inject(UserService);
  private historySvc = inject(HistoryService);
  private statsSvc = inject(StatsService);
  private ui = inject(UiPreferencesService);
  private i18n = inject(I18nService);

  isLoading = signal(true);
  searchQuery = signal('');
  historyPage = signal(1);
  pageSize = 8;

  profile = signal<UserProfile | null>(null);
  listenHistory = signal<ListenRecord[]>([]);

  weekLabels = [
    { x: 10, label: 'Lun' }, { x: 60, label: 'Mar' }, { x: 110, label: 'Mié' },
    { x: 160, label: 'Jue' }, { x: 210, label: 'Vie' }, { x: 260, label: 'Sáb' }, { x: 310, label: 'Dom' },
  ];

  activityData = signal<number[]>([0, 0, 0, 0, 0, 0, 0]);
  devices = signal<{ id: string; name: string; platform: string; lastAccess: string; online: boolean; iconKey: string }[]>([]);

  private translatePlan(plan: string): string {
    if (plan === 'Free') return this.i18n.t('shell.planFree');
    const map: Record<string, string> = {
      Demo: 'Demo',
      Premium: 'Premium',
    };
    return map[plan] ?? plan;
  }

  displayProfile = computed(() => {
    this.i18n.tick();
    const p = this.profile();
    if (!p) {
      return {
        name: 'Usuario',
        username: '@user',
        plan: this.i18n.t('shell.planFree'),
        initial: 'U',
        avatarGradient: COVER_GRADIENTS[0],
        badges: ['Oyente'],
        lastActive: '—',
        registered: '—',
      };
    }
    const planLabel = this.translatePlan(p.plan);
    return {
      name: p.username,
      username: `@${p.username}`,
      plan: planLabel,
      initial: p.username.charAt(0).toUpperCase(),
      avatarGradient: COVER_GRADIENTS[p.id % COVER_GRADIENTS.length],
      badges: [planLabel, p.favorite_genre ?? 'Multi-género'].filter(Boolean),
      lastActive: 'Activo ahora',
      registered: p.created_at ? new Date(p.created_at).toLocaleDateString('es') : '—',
    };
  });

  preferences = computed(() => {
    const p = this.profile();
    const prefs = p?.preferences;
    return {
      favoriteGenre: p?.favorite_genre ?? '—',
      audioQuality: AUDIO_LABELS[prefs?.audio_quality ?? 'high'] ?? 'Alta',
      personalizedRecs: prefs?.recommendations_enabled ?? true,
      darkMode: prefs?.dark_mode ?? true,
      privacyPublic: prefs?.privacy_public ?? false,
    };
  });


  favoritePlaylists = computed((): PlaylistCard[] => {
    const pls = this.profile()?.playlists ?? [];
    return pls.map((pl, i) => ({
      id: pl.id,
      name: pl.name,
      tracks: pl.total_tracks,
      gradient: COVER_GRADIENTS[i % COVER_GRADIENTS.length],
    }));
  });

  stats = computed(() => ({
    favorites: this.profile()?.stats?.favorites_count ?? 0,
    playlists: this.profile()?.stats?.playlists_count ?? 0,
  }));

  topArtists = computed((): TopItem[] => {
    const counts = new Map<string, number>();
    for (const h of this.listenHistory()) {
      if (h.artist && h.artist !== '—') {
        counts.set(h.artist, (counts.get(h.artist) ?? 0) + 1);
      }
    }
    const colors = ['#1ed896', '#7c3aed', '#10b981', '#3b82f6', '#ec4899'];
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value], i) => ({ name, value, color: colors[i % colors.length] }));
  });

  topGenres = computed((): TopItem[] => {
    const genre = this.profile()?.favorite_genre;
    if (!genre) return [{ name: 'Sin datos', value: 0, color: '#1ed896' }];
    return [{ name: genre, value: 100, color: '#1ed896' }];
  });

  activities = computed((): ActivityItem[] => {
    const items: ActivityItem[] = [];
    const hist = this.historySvc.getRecent(3);
    hist.forEach((h, i) => {
      items.push({
        id: i + 1,
        type: 'play',
        title: 'Escuchado',
        detail: h.nombre_track,
        time: this.formatRelative(h.viewed_at),
        iconKey: 'play',
      });
    });
    const fav = this.stats().favorites;
    if (fav > 0) {
      items.push({
        id: 99,
        type: 'favorite',
        title: 'Favoritos',
        detail: `${fav} tracks guardados`,
        time: 'Reciente',
        iconKey: 'heart',
      });
    }
    return items.length ? items : [{
      id: 1, type: 'session', title: 'Sesión', detail: 'Web Player', time: 'Hoy', iconKey: 'globe',
    }];
  });

  recentCarousel = computed((): RecentItem[] =>
    this.listenHistory().slice(0, 8).map((r, i) => ({
      ...r,
      coverGradient: COVER_GRADIENTS[i % COVER_GRADIENTS.length],
    }))
  );

  filteredHistory = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    if (!q) return this.listenHistory();
    return this.listenHistory().filter(
      (r) => r.track.toLowerCase().includes(q) || r.artist.toLowerCase().includes(q)
    );
  });

  totalHistoryPages = computed(() => Math.max(1, Math.ceil(this.filteredHistory().length / this.pageSize)));

  pagedHistory = computed(() => {
    const start = (this.historyPage() - 1) * this.pageSize;
    return this.filteredHistory().slice(start, start + this.pageSize);
  });

  maxTopValue = computed(() =>
    Math.max(...this.topArtists().map((x) => x.value), ...this.topGenres().map((x) => x.value), 1)
  );

  activityPoints = computed(() =>
    this.activityData().map((v, i) => ({ x: 10 + i * 50, y: 88 - Math.min(v, 100) * 0.75 }))
  );

  ngOnInit() {
    this.historySvc.reload();
    this.loadHistoryFromStorage();
    this.userSvc.getMe().subscribe({
      next: (p) => {
        this.profile.set(p);
        if (p.preferences?.dark_mode != null) {
          this.ui.syncThemeFromDarkMode(p.preferences.dark_mode);
        }
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false),
    });

    this.statsSvc.getTrendingAnalytics(7).subscribe({
      next: (d) => {
        const vals = (d.daily_streams ?? []).slice(-7).map((x) => {
          const max = Math.max(...(d.daily_streams ?? []).map((s) => s.total_streams ?? 0), 1);
          return Math.round(((x.total_streams ?? 0) / max) * 100);
        });
        if (vals.length) this.activityData.set(vals);
      },
    });

    this.statsSvc.getPlatformAnalytics().subscribe({
      next: (d) => {
        const devs = (d.devices ?? []).slice(0, 4).map((dev, i) => ({
          id: dev.device_type ?? `dev-${i}`,
          name: dev.device_type ?? 'Dispositivo',
          platform: `${dev.device_type ?? '—'} · ${dev.stream_count ?? 0} streams`,
          lastAccess: 'Sesión activa',
          online: i === 0,
          iconKey: i === 0 ? 'monitor' : 'smartphone',
        }));
        if (devs.length) {
          this.devices.set(devs);
        } else {
          this.devices.set([
            { id: 'web', name: 'Web Player', platform: 'VOXMETRIK SPA', lastAccess: 'Ahora', online: true, iconKey: 'monitor' },
          ]);
        }
      },
    });
  }

  private loadHistoryFromStorage() {
    const entries = this.historySvc.getRecent(20);
    this.listenHistory.set(entries.map((e, i) => this.historyToRecord(e, i)));
  }

  private historyToRecord(e: HistoryEntry, i: number): ListenRecord {
    const d = new Date(e.viewed_at);
    return {
      id: e.id_track || i + 1,
      track: e.nombre_track,
      artist: e.nombre_artista ?? '—',
      genre: '—',
      duration: '—',
      playedAt: d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }),
    };
  }

  private formatRelative(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `Hace ${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `Hace ${hrs}h`;
    return 'Ayer';
  }

  onSearchChange(value: string) {
    this.searchQuery.set(value);
    this.historyPage.set(1);
  }

  goHistoryPage(p: number) {
    if (p < 1 || p > this.totalHistoryPages()) return;
    this.historyPage.set(p);
  }

  barWidth(value: number): number {
    return Math.round((value / this.maxTopValue()) * 100);
  }

  coverGradient(id: number): string {
    return COVER_GRADIENTS[(id - 1) % COVER_GRADIENTS.length];
  }

  trackInitial(name: string): string {
    return name.charAt(0).toUpperCase();
  }

  activityLine(): string {
    return this.activityPoints().map((p) => `${p.x},${p.y}`).join(' ');
  }

  activityArea(): string {
    const pts = this.activityPoints();
    if (!pts.length) return '';
    const line = pts.map((p) => `${p.x},${p.y}`).join(' ');
    return `${pts[0].x},88 ${line} ${pts[pts.length - 1].x},88`;
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
