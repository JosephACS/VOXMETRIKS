import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject, Input, OnInit, OnChanges, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FavoritesStore } from '../../../playback-core/favorites.store';
import { NotificationService } from '../../../core/services/notification.service';
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
      [class.active]="active()"
      [class.pop]="pop()"
      [class.sm]="size === 'sm'"
      (click)="onToggle($event)"
      [title]="labelKey | t"
      [attr.aria-label]="labelKey | t"
      [attr.aria-pressed]="active()"
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
export class FavoriteBtnComponent implements OnInit, OnChanges {
  readonly lang = inject(I18nService).lang;
  @Input({ required: true }) trackId!: number;
  @Input() size: 'sm' | 'md' = 'md';

  private favs = inject(FavoritesStore);
  private icons = inject(IconRenderService);
  private notify = inject(NotificationService);

  private trackIdSig = signal(0);
  active = computed(() => this.favs.favoriteIds().has(this.trackIdSig()));
  pop = signal(false);
  iconSvg: SafeHtml = '';

  get labelKey(): TranslationKey {
    return this.active() ? 'favorite.remove' : 'favorite.add';
  }

  ngOnInit() {
    this.iconSvg = this.icons.render('heart', 16);
    this.trackIdSig.set(this.trackId);
  }

  ngOnChanges() {
    if (this.trackId != null) this.trackIdSig.set(this.trackId);
  }

  onToggle(event: Event) {
    event.stopPropagation();
    event.preventDefault();
    this.pop.set(true);
    window.setTimeout(() => this.pop.set(false), 420);
    const wasActive = this.active();
    this.favs.toggle(this.trackId).subscribe({
      next: () => {
        if (!wasActive) {
          this.notify.success('Agregado a favoritos');
        }
      },
    });
  }
}
