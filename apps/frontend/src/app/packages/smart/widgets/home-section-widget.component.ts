import { Component, input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { I18nService } from '../../../core/services/i18n.service';
import {
  resolveSectionSubtitle,
  resolveSectionTitle,
  translateReasonCode,
  translateSystemCode,
} from '../../../core/i18n/system-labels';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { SmartHomeSection, smartItemToTrack } from '../models/smart-home.models';
import { Track } from '../../../shared/models/api.models';

@Component({
  selector: 'app-home-section-widget',
  standalone: true,
  imports: [CommonModule, RouterModule, HorizontalSectionComponent, MediaCardComponent],
  template: `
    @if (tracks().length) {
      <app-horizontal-section
        [title]="displayTitle()"
        [subtitle]="displaySubtitle()"
        [link]="sectionLink()"
      >
        @for (t of tracks(); track t.id_track; let i = $index) {
          <app-media-card
            [title]="cleanTitle(t.nombre_track)"
            [subtitle]="t.nombre_artista ?? '—'"
            [gradient]="cover(t.id_track)"
            [coverTrackId]="t.id_track"
            [coverArtistId]="t.id_artista"
            [imageUrl]="coverUrlFor(t.id_track)"
            [link]="'/tracks/' + t.id_track"
            [track]="controller.fromTrack(t)"
            [queue]="playableQueue()"
            [tag]="tagFor(i)"
            [meta]="metaFor(t)"
          />
        }
      </app-horizontal-section>
    }
  `,
})
export class HomeSectionWidgetComponent {
  readonly section = input.required<SmartHomeSection>();
  private readonly covers = inject(CoverArtService);
  private readonly i18n = inject(I18nService);
  readonly controller = inject(PlayerController);

  readonly tracks = computed(() =>
    this.section().tracks.map(smartItemToTrack),
  );

  readonly playableQueue = computed(() =>
    this.tracks().map((t) => this.controller.fromTrack(t)),
  );

  /** Recompute when language changes (i18n.lang). */
  readonly displayTitle = computed(() => {
    this.i18n.lang();
    return resolveSectionTitle(this.section(), (k, p) => this.i18n.t(k, p));
  });

  readonly displaySubtitle = computed(() => {
    this.i18n.lang();
    return resolveSectionSubtitle(this.section(), (k, p) => this.i18n.t(k, p));
  });

  sectionLink = computed(() => {
    const s = this.section();
    if (s.type === 'playlist') return '/playlists';
    if (s.id === 'recommended-for-you' || s.code === 'recommended_for_you') {
      return '/recommendations';
    }
    return undefined;
  });

  cleanTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }

  cover(id: number): string {
    return this.covers.gradientFor(id);
  }

  coverUrlFor(trackId: number): string | null {
    const raw = this.section().tracks.find((x) => x.id_track === trackId);
    return raw?.cover_url ?? null;
  }

  tagFor(index: number): string | undefined {
    this.i18n.lang();
    const s = this.section();
    const t = (k: string) => this.i18n.t(k);
    if (s.type === 'because') return translateSystemCode('tag_because', t) ?? undefined;
    if (s.type === 'playlist') return translateSystemCode('tag_mix', t) ?? undefined;
    if (index === 0) return translateSystemCode('tag_for_you', t) ?? undefined;
    return undefined;
  }

  metaFor(t: Track): string | undefined {
    this.i18n.lang();
    const raw = this.section().tracks.find((x) => x.id_track === t.id_track);
    const translate = (k: string, p?: Record<string, string | number>) =>
      this.i18n.t(k, p);

    if (raw?.reason) {
      return translateReasonCode(raw.reason, translate) ?? undefined;
    }
    if (raw?.mix_tag) {
      return translateReasonCode(raw.mix_tag, translate) ?? undefined;
    }
    if (raw?.score != null) {
      return translateSystemCode('meta_match', translate, {
        pct: Math.round(raw.score * 100),
      }) ?? undefined;
    }
    if (raw?.similarity != null) {
      return translateSystemCode('meta_similar', translate, {
        pct: Math.round(raw.similarity * 100),
      }) ?? undefined;
    }
    return undefined;
  }
}
