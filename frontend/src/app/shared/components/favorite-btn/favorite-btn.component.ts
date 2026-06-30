import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, Input, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
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
      [class.pop]="pop()"
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
    }
    .fav-btn.sm { width: 28px; height: 28px; }
    .fav-btn:hover { color: #ef4444; border-color: rgba(239,68,68,0.35); }
    .fav-btn.active { color: #ef4444; border-color: rgba(239,68,68,0.45); background: rgba(239,68,68,0.1); }
    .fav-btn.pop.active { box-shadow: 0 0 0 4px rgba(239,68,68,0.12); }
  `],
})
export class FavoriteBtnComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  @Input({ required: true }) trackId!: number;
  @Input() size: 'sm' | 'md' = 'md';

  private favs = inject(FavoritesService);
  private icons = inject(IconRenderService);
  private destroyRef = inject(DestroyRef);

  active = false;
  pop = signal(false);
  iconSvg: SafeHtml = '';

  get labelKey(): TranslationKey {
    return this.active ? 'favorite.remove' : 'favorite.add';
  }

  ngOnInit() {
    this.iconSvg = this.icons.render('heart', 16);
    this.favs.favoriteIds$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((ids) => {
        this.active = ids.has(this.trackId);
      });
  }

  onToggle(event: Event) {
    event.stopPropagation();
    event.preventDefault();
    this.pop.set(true);
    window.setTimeout(() => this.pop.set(false), 420);
    this.favs.toggle(this.trackId).subscribe();
  }
}
