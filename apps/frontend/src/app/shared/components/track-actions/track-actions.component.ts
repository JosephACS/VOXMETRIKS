import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlayableTrack } from '../../models/player.models';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { TrackContextMenuComponent } from '../track-context-menu/track-context-menu.component';

/** Reusable favorite + queue/playlist context actions for any track surface. */
@Component({
  selector: 'app-track-actions',
  standalone: true,
  imports: [CommonModule, FavoriteBtnComponent, TrackContextMenuComponent],
  template: `
    <div class="track-actions" (click)="$event.stopPropagation()">
      <app-favorite-btn [trackId]="track.id" [size]="size" />
      <app-track-context-menu
        [track]="track"
        [contextQueue]="queue"
        [artistId]="artistId ?? track.artistId"
        [size]="size"
        [dropUp]="dropUp"
      />
    </div>
  `,
  styles: [`
    .track-actions {
      display: inline-flex;
      align-items: center;
      gap: 0.15rem;
    }
  `],
})
export class TrackActionsComponent {
  @Input({ required: true }) track!: PlayableTrack;
  @Input() queue: PlayableTrack[] = [];
  @Input() artistId?: number;
  @Input() size: 'sm' | 'md' = 'md';
  @Input() dropUp = false;
}
