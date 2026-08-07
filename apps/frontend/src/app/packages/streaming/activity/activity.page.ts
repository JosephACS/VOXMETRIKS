import {
  Component,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import {
  ActivityPeriod,
  ListeningActivityResponse,
  ListeningActivityService,
} from '../services/listening-activity.service';
import { PlayerController } from '../../../playback-core/player.controller';
import { toPlayableFromHistory } from '../../../playback-core/adapters/track.adapter';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { I18nService } from '../../../core/services/i18n.service';
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { HistoryEntry } from '../../../shared/models/api.models';

@Component({
  selector: 'app-activity-page',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  templateUrl: './activity.page.html',
  styleUrls: ['./activity.page.css'],
})
export class ActivityPageComponent implements OnInit, OnDestroy {
  readonly lang = inject(I18nService).lang;
  private api = inject(ListeningActivityService);
  private controller = inject(PlayerController);
  private trackCover = inject(TrackCoverService);
  private covers = inject(CoverArtService);
  private sub?: Subscription;

  period = signal<ActivityPeriod>('30d');
  loading = signal(true);
  error = signal(false);
  data = signal<ListeningActivityResponse | null>(null);
  coverUrls = signal<Record<number, string>>({});

  readonly periods: { id: ActivityPeriod; labelKey: string }[] = [
    { id: '7d', labelKey: 'activity.period.7d' },
    { id: '30d', labelKey: 'activity.period.30d' },
    { id: '90d', labelKey: 'activity.period.90d' },
    { id: 'all', labelKey: 'activity.period.all' },
  ];

  empty = computed(() => !!this.data()?.empty);
  summary = computed(() => this.data()?.summary);
  topTracks = computed(() => this.data()?.top_tracks ?? []);
  topArtists = computed(() => this.data()?.top_artists ?? []);
  topGenres = computed(() => this.data()?.top_genres ?? []);
  timeline = computed(() => this.data()?.timeline ?? []);
  recent = computed(() => this.data()?.recent ?? []);
  maxTimelinePlays = computed(() =>
    Math.max(1, ...this.timeline().map((d) => d.plays || 0)),
  );

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  setPeriod(p: ActivityPeriod): void {
    if (this.period() === p) return;
    this.period.set(p);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.sub?.unsubscribe();
    this.sub = this.api.getActivity(this.period()).subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
        const ids = [
          ...res.top_tracks.map((t) => t.id_track),
          ...res.recent.map((t) => t.id_track),
        ];
        for (const id of [...new Set(ids)].slice(0, 40)) {
          this.trackCover.bestCover$(id).subscribe((url) => {
            if (url) this.coverUrls.update((m) => ({ ...m, [id]: url }));
          });
        }
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  titleOf(t: { nombre_track?: string }): string {
    return displayTrackTitle(t.nombre_track || '');
  }

  artistOf(t: { nombre_artista?: string }): string {
    return primaryArtistName(t.nombre_artista || '') || '—';
  }

  cover(id: number): string | null {
    return this.coverUrls()[id] || null;
  }

  playTrack(row: {
    id_track: number;
    nombre_track?: string;
    nombre_artista?: string;
    source_unavailable?: boolean;
    duration_ms?: number;
  }): void {
    if (row.source_unavailable) return;
    const entry = {
      id_track: row.id_track,
      nombre_track: row.nombre_track || '',
      nombre_artista: row.nombre_artista,
      duration_ms: row.duration_ms,
    } as HistoryEntry;
    const playable = toPlayableFromHistory(this.covers, entry);
    const queue = this.topTracks()
      .filter((t) => !t.source_unavailable)
      .map((t) =>
        toPlayableFromHistory(this.covers, {
          id_track: t.id_track,
          nombre_track: t.nombre_track || '',
          nombre_artista: t.nombre_artista,
          duration_ms: t.duration_ms,
        } as HistoryEntry),
      );
    this.controller.playTrack(playable, queue.length ? queue : [playable]);
  }
}
