import { SafeHtml } from '@angular/platform-browser';
import { Component, HostListener, Input, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IconRenderService } from '../../services/icon-render.service';
import { PlaylistsService } from '../../../packages/streaming/services/playlists.service';
import { PlaylistSummary } from '../../models/api.models';
import { TranslatePipe } from '../../pipes/translate.pipe';

@Component({
  selector: 'app-add-to-playlist-btn',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  templateUrl: './add-to-playlist-btn.component.html',
  styleUrls: ['./add-to-playlist-btn.component.css'],
})
export class AddToPlaylistBtnComponent {
  private iconRender = inject(IconRenderService);
  private playlistsSvc = inject(PlaylistsService);

  @Input({ required: true }) trackId!: number;
  @Input() size: 'sm' | 'md' = 'md';
  @Input() dropUp = false;
  @Input() variant: 'icon' | 'button' = 'icon';

  open = signal(false);
  playlists = signal<PlaylistSummary[]>([]);
  msg = signal('');
  loaded = signal(false);

  toggle(e: Event) {
    e.preventDefault();
    e.stopPropagation();
    const next = !this.open();
    this.open.set(next);
    this.msg.set('');
    if (next && !this.loaded()) {
      this.playlistsSvc.list().subscribe({
        next: (d) => {
          this.playlists.set(d ?? []);
          this.loaded.set(true);
        },
        error: () => this.playlists.set([]),
      });
    }
  }

  add(plId: number, e: Event) {
    e.preventDefault();
    e.stopPropagation();
    this.playlistsSvc.addTrack(plId, this.trackId).subscribe({
      next: () => {
        this.msg.set('ok');
        setTimeout(() => {
          this.open.set(false);
          this.msg.set('');
        }, 900);
      },
      error: () => this.msg.set('err'),
    });
  }

  @HostListener('document:click')
  closeOnOutside() {
    if (this.open()) this.open.set(false);
  }

  icon(size = 14): SafeHtml {
    return this.iconRender.render('playlist', size);
  }
}
