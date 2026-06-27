import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FavoritesService } from '../../../packages/streaming/services/favorites.service';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { TranslationKey } from '../../../core/i18n/translations';

@Component({
  selector: 'app-favorite-btn',
  standalone: true,
  imports: [CommonModule, TranslatePipe],
  template: `
    <button
      type="button"
      class="fav-btn"
      [class.active]="active"
      [class.sm]="size === 'sm'"
      (click)="onToggle($event)"
      [title]="labelKey | t"
      [attr.aria-label]="labelKey | t"
      [attr.aria-pressed]="active"
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
      border: 1px solid var(--border, rgba(255,255,255,0.08));
      border-radius: 50%;
      background: transparent;
      color: var(--text-muted, rgba(255,255,255,0.55));
      cursor: pointer;
      transition: all 150ms;
    }
    .fav-btn.sm { width: 28px; height: 28px; }
    .fav-btn:hover { color: #ef4444; border-color: rgba(239,68,68,0.35); }
    .fav-btn.active { color: #ef4444; border-color: rgba(239,68,68,0.45); background: rgba(239,68,68,0.1); }
  `],
})
export class FavoriteBtnComponent implements OnInit {
  @Input({ required: true }) trackId!: number;
  @Input() size: 'sm' | 'md' = 'md';

  private favs = inject(FavoritesService);
  private icons = inject(IconRenderService);

  active = false;
  iconSvg: SafeHtml = '';

  get labelKey(): TranslationKey {
    return this.active ? 'favorite.remove' : 'favorite.add';
  }

  ngOnInit() {
    this.iconSvg = this.icons.render('heart', 16);
    this.favs.favoriteIds$.subscribe((ids) => {
      this.active = ids.has(this.trackId);
    });
  }

  onToggle(event: Event) {
    event.stopPropagation();
    event.preventDefault();
    this.favs.toggle(this.trackId).subscribe();
  }
}
