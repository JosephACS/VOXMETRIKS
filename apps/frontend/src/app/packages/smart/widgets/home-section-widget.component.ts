import { Component, input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HorizontalSectionComponent } from '../../../shared/components/horizontal-section/horizontal-section.component';
import { MediaCardComponent } from '../../../shared/components/media-card/media-card.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { SmartHomeSection, smartItemToTrack } from '../models/smart-home.models';
import { Track } from '../../../shared/models/api.models';
import { PlayableTrack } from '../../../shared/models/player.models';

@Component({
  selector: 'app-home-section-widget',
  standalone: true,
  imports: [CommonModule, RouterModule, HorizontalSectionComponent, MediaCardComponent],
  template: `
    @if (tracks().length) {
      <app-horizontal-section
        [title]="section().title"
        [subtitle]="section().subtitle ?? ''"
        [link]="sectionLink()"
      >
        @for (t of tracks(); track t.id_track; let i = $index) {
          <app-media-card
            [title]="cleanTitle(t.nombre_track)"
            [subtitle]="t.nombre_artista ?? '—'"
            [gradient]="cover(t.id_track)"
            [coverTrackId]="t.id_track"
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
  readonly controller = inject(PlayerController);

  readonly tracks = computed(() =>
    this.section().tracks.map(smartItemToTrack),
  );

  readonly playableQueue = computed(() =>
    this.tracks().map((t) => this.controller.fromTrack(t)),
  );

  sectionLink = computed(() => {
    const s = this.section();
    if (s.type === 'playlist') return '/playlists';
    if (s.id === 'recommended-for-you') return '/recommendations';
    return undefined;
  });

  cleanTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }

  cover(id: number): string {
    return this.covers.gradientFor(id);
  }

  tagFor(index: number): string | undefined {
    const s = this.section();
    if (s.type === 'because') return 'Because you';
    if (s.type === 'playlist') return 'Mix';
    if (index === 0) return 'For you';
    return undefined;
  }

  metaFor(t: Track): string | undefined {
    const raw = this.section().tracks.find((x) => x.id_track === t.id_track);
    if (raw?.reason) return raw.reason.replace(/_/g, ' ');
    if (raw?.score != null) return `${Math.round(raw.score * 100)}% match`;
    if (raw?.similarity != null) return `${Math.round(raw.similarity * 100)}% similar`;
    return undefined;
  }
}
