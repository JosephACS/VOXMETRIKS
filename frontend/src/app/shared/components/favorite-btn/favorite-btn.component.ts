import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FavoritesService } from '../../../packages/streaming/services/favorites.service';

@Component({
  selector: 'app-favorite-btn',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      type="button"
      class="fav-btn"
      [class.active]="active"
      [class.sm]="size === 'sm'"
      (click)="onToggle($event)"
      [title]="active ? 'Quitar de favoritos' : 'Agregar a favoritos'"
    >
      <span [innerHTML]="iconSvg" aria-hidden="true"></span>
    </button>
  `,
  styles: [`
    .fav-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 50%;
      background: rgba(255,255,255,0.04);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;
      padding: 0;
    }
    .fav-btn.sm { width: 28px; height: 28px; }
    .fav-btn:hover { border-color: rgba(239,68,68,0.4); color: #ef4444; background: rgba(239,68,68,0.08); }
    .fav-btn.active { color: #ef4444; border-color: rgba(239,68,68,0.45); background: rgba(239,68,68,0.12); }
    .fav-btn :deep(svg) { width: 14px; height: 14px; }
    .fav-btn.sm :deep(svg) { width: 12px; height: 12px; }
  `],
})
export class FavoriteBtnComponent implements OnInit {
  private iconRender = inject(IconRenderService);

  @Input({ required: true }) trackId!: number;
  @Input() size: 'sm' | 'md' = 'md';

  private favSvc = inject(FavoritesService);
  active = false;

  ngOnInit() {
    this.active = this.favSvc.isFavorite(this.trackId);
    this.favSvc.favoriteIds$.subscribe((ids) => {
      this.active = ids.has(this.trackId);
    });
  }

  get iconSvg(): SafeHtml {
    return this.iconRender.render('heart', this.size === 'sm' ? 12 : 14);
  }

  onToggle(e: Event) {
    e.preventDefault();
    e.stopPropagation();
    this.favSvc.toggle(this.trackId).subscribe({
      next: () => { this.active = this.favSvc.isFavorite(this.trackId); },
      error: () => {},
    });
  }
}
