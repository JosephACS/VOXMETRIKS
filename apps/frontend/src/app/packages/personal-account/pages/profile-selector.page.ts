import { CommonModule } from '@angular/common';
import { Component, HostListener, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { BrandMarkComponent } from '../../../shared/components/brand-mark/brand-mark.component';
import { FavoritesService } from '../../streaming/services/favorites.service';
import { HistoryService } from '../../streaming/services/history.service';
import { PersonalAccountApiService } from '../services/personal-account-api.service';
import { ProfileSwitchService } from '../services/profile-switch.service';
import { SecurityApiService, PinStatus } from '../services/security-api.service';
import { TrustedDeviceService } from '../services/trusted-device.service';

interface ProfileCard {
  profile_key?: string;
  user_id: number;
  display_name: string;
  initials: string;
  avatar_hue: number;
  avatar_url?: string | null;
  role: string;
  is_me?: boolean;
  pin_enabled?: boolean;
}

type PinModalMode = 'self' | 'other';

@Component({
  selector: 'app-profile-selector-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, BrandMarkComponent],
  styleUrl: './profile-selector.page.css',
  template: `
    <div
      class="who-listening"
      [class.who-listening--leaving]="leaving()"
      data-testid="who-listening-page"
    >
      <header class="who-listening__brand">
        <app-brand-mark variant="horizontal" ariaLabel="VOXMETRIKS" />
      </header>

      <div class="who-listening__hero">
        <h1>{{ 'personal.profiles.title' | t:lang() }}</h1>
        <p class="who-listening__subtitle">{{ 'personal.profiles.chooseSubtitle' | t:lang() }}</p>
      </div>

      @if (loading()) {
        <div class="who-listening__loading" role="status">{{ 'common.loading' | t:lang() }}</div>
      } @else if (error()) {
        <div class="who-listening__error" role="alert">
          <p>{{ error() }}</p>
          <div class="who-listening__actions">
            <button type="button" class="wl-btn wl-btn--primary" (click)="load()">
              {{ 'common.retry' | t:lang() }}
            </button>
            <button type="button" class="wl-btn wl-btn--ghost" (click)="exit()">
              {{ 'personal.profiles.exit' | t:lang() }}
            </button>
          </div>
        </div>
      } @else {
        @if (!planActive()) {
          <p class="who-listening__banner" role="status">
            {{ 'personal.profiles.planInactive' | t:lang() }}
          </p>
        }

        <div
          class="who-listening__grid"
          role="listbox"
          [attr.aria-label]="'personal.profiles.title' | t:lang()"
        >
          @for (p of profiles(); track p.user_id; let i = $index) {
            <button
              type="button"
              class="wl-card"
              role="option"
              [attr.aria-selected]="focusIndex() === i"
              [class.wl-card--focused]="focusIndex() === i"
              [class.wl-card--selected]="selectedId() === p.user_id"
              [class.wl-card--me]="p.is_me"
              [style.animation-delay]="i * 60 + 'ms'"
              (click)="select(p)"
              (mouseenter)="focusIndex.set(i)"
              (focus)="focusIndex.set(i)"
            >
              <span
                class="wl-avatar"
                [style.background]="
                  p.avatar_url ? 'transparent' : 'hsl(' + p.avatar_hue + ' 48% 36%)'
                "
              >
                @if (p.avatar_url) {
                  <img [src]="p.avatar_url" [alt]="p.display_name" />
                } @else {
                  {{ p.initials }}
                }
                @if (p.pin_enabled) {
                  <span class="wl-card__lock" aria-hidden="true" title="PIN">&#128274;</span>
                }
              </span>
              <span class="wl-card__name">{{ p.display_name }}</span>
              <span class="wl-card__role">{{ roleLabel(p.role) }}</span>
              @if (p.is_me) {
                <span class="wl-card__you">{{ 'personal.profiles.yourProfile' | t:lang() }}</span>
              }
            </button>
          }
        </div>

        <div class="who-listening__footer">
          <label class="wl-check">
            <input
              type="checkbox"
              [checked]="remember()"
              (change)="toggleRemember($event)"
            />
            <span>{{ 'personal.profiles.rememberDevice' | t:lang() }}</span>
          </label>

          <div class="who-listening__actions">
            <a routerLink="/account/household" class="wl-btn wl-btn--ghost">{{
              'personal.profiles.manageProfiles' | t:lang()
            }}</a>
            @if (!planActive()) {
              <a routerLink="/account/subscription" class="wl-btn wl-btn--primary">{{
                'personal.profiles.reviewPlan' | t:lang()
              }}</a>
            }
            <button type="button" class="wl-btn wl-btn--ghost" (click)="exit()">
              {{ 'personal.profiles.exit' | t:lang() }}
            </button>
          </div>
        </div>
      }

      @if (switchTarget(); as target) {
        <div
          class="wl-modal-backdrop"
          role="presentation"
          (click)="cancelSwitch()"
        >
          <div
            class="wl-modal"
            role="dialog"
            aria-modal="true"
            [attr.aria-labelledby]="'wl-switch-title'"
            (click)="$event.stopPropagation()"
          >
            <h2 id="wl-switch-title">{{ 'personal.profiles.switchTitle' | t:lang() }}</h2>
            <p>{{ 'personal.profiles.switchBody' | t:lang() }}</p>
            <p class="wl-modal__name">{{ target.display_name }}</p>
            <div class="who-listening__actions">
              <button
                type="button"
                class="wl-btn wl-btn--primary"
                [disabled]="switching()"
                (click)="confirmSwitch()"
              >
                {{ 'personal.profiles.switchContinue' | t:lang() }}
              </button>
              <button type="button" class="wl-btn wl-btn--ghost" (click)="cancelSwitch()">
                {{ 'common.cancel' | t:lang() }}
              </button>
            </div>
          </div>
        </div>
      }

      @if (pinTarget(); as target) {
        <div
          class="wl-modal-backdrop wl-modal-backdrop--pin"
          role="presentation"
          (click)="cancelPin()"
        >
          <div
            class="wl-modal wl-modal--pin"
            role="dialog"
            aria-modal="true"
            [attr.aria-labelledby]="'wl-pin-title'"
            (click)="$event.stopPropagation()"
          >
            <div class="wl-pin-hero">
              <span
                class="wl-pin-avatar"
                [style.background]="
                  target.avatar_url ? 'transparent' : 'hsl(' + target.avatar_hue + ' 48% 36%)'
                "
              >
                @if (target.avatar_url) {
                  <img [src]="target.avatar_url" [alt]="target.display_name" />
                } @else {
                  {{ target.initials }}
                }
              </span>
              <p class="wl-pin-name">{{ target.display_name }}</p>
            </div>

            <h2 id="wl-pin-title">{{ 'personal.profiles.pinTitle' | t:lang() }}</h2>
            <p class="wl-pin-body">{{ 'personal.profiles.pinBody' | t:lang() }}</p>

            @if (pinLocked()) {
              <p class="wl-pin-error" role="alert">{{ 'personal.profiles.pinLocked' | t:lang() }}</p>
            } @else {
              <div class="wl-pin-input-wrap">
                <input
                  #pinInput
                  class="wl-pin-input"
                  [type]="pinVisible() ? 'text' : 'password'"
                  inputmode="numeric"
                  pattern="[0-9]*"
                  maxlength="6"
                  autocomplete="off"
                  [attr.aria-label]="'personal.profiles.pinTitle' | t:lang()"
                  [disabled]="pinSubmitting()"
                  [(ngModel)]="pinValue"
                  (keydown.enter)="submitPin()"
                />
                <button
                  type="button"
                  class="wl-pin-toggle"
                  [attr.aria-pressed]="pinVisible()"
                  (click)="pinVisible.set(!pinVisible())"
                >
                  {{ pinVisible() ? ('personal.profiles.pinHide' | t:lang()) : ('personal.profiles.pinShow' | t:lang()) }}
                </button>
              </div>

              <div class="wl-pin-keypad" aria-hidden="true">
                @for (digit of keypadDigits; track digit) {
                  <button
                    type="button"
                    class="wl-pin-key"
                    [disabled]="pinSubmitting()"
                    (click)="appendPinDigit(digit)"
                  >
                    {{ digit }}
                  </button>
                }
                <button
                  type="button"
                  class="wl-pin-key wl-pin-key--wide"
                  [disabled]="pinSubmitting()"
                  (click)="backspacePin()"
                >
                  &#9003;
                </button>
              </div>

              @if (pinError()) {
                <p class="wl-pin-error" role="alert">{{ pinError() }}</p>
              }
            }

            <div class="who-listening__actions wl-pin-actions">
              @if (!pinLocked()) {
                <button
                  type="button"
                  class="wl-btn wl-btn--primary"
                  [disabled]="pinSubmitting() || !pinValue.trim()"
                  (click)="submitPin()"
                >
                  {{ 'personal.profiles.pinContinue' | t:lang() }}
                </button>
              }
              <button type="button" class="wl-btn wl-btn--ghost" (click)="cancelPin()">
                {{ 'common.cancel' | t:lang() }}
              </button>
              <button type="button" class="wl-btn wl-btn--link" (click)="forgotPin()">
                {{ 'personal.profiles.pinForgot' | t:lang() }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
})
export class ProfileSelectorPage implements OnInit {
  private api = inject(PersonalAccountApiService);
  private i18n = inject(I18nService);
  private profileSwitch = inject(ProfileSwitchService);
  private securityApi = inject(SecurityApiService);
  private trustedDevice = inject(TrustedDeviceService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private favorites = inject(FavoritesService, { optional: true });
  private history = inject(HistoryService, { optional: true });
  readonly lang = this.i18n.lang;

  readonly keypadDigits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];

  profiles = signal<ProfileCard[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  remember = signal(false);
  planActive = signal(true);
  focusIndex = signal(0);
  selectedId = signal<number | null>(null);
  leaving = signal(false);
  switchTarget = signal<ProfileCard | null>(null);
  switching = signal(false);

  pinTarget = signal<ProfileCard | null>(null);
  pinMode = signal<PinModalMode>('self');
  pinValue = '';
  pinVisible = signal(false);
  pinSubmitting = signal(false);
  pinError = signal<string | null>(null);
  pinLocked = signal(false);
  private pinStatusCache: PinStatus | null = null;

  private returnUrl = '/discover';

  ngOnInit(): void {
    this.remember.set(this.profileSwitch.isRememberProfile());
    const ret = this.route.snapshot.queryParamMap.get('returnUrl');
    if (ret && ret.startsWith('/') && !ret.startsWith('//')) {
      this.returnUrl = ret;
    }
    this.load();
  }

  @HostListener('keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    const list = this.profiles();
    if (!list.length || this.switchTarget() || this.pinTarget()) return;
    const i = this.focusIndex();
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      this.focusIndex.set((i + 1) % list.length);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      this.focusIndex.set((i - 1 + list.length) % list.length);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.select(list[this.focusIndex()]);
    } else if (event.key === 'Escape') {
      if (this.pinTarget()) this.cancelPin();
      else if (this.switchTarget()) this.cancelSwitch();
    }
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.getProfiles().subscribe({
      next: (res) => {
        this.profiles.set(res.profiles || []);
        this.planActive.set(res.plan_active !== false);
        this.loading.set(false);
        const me = (res.profiles || []).findIndex((p) => p.is_me);
        this.focusIndex.set(me >= 0 ? me : 0);
        if (!(res.profiles || []).length) {
          void this.enterApp();
        }
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
        this.loading.set(false);
      },
    });
  }

  roleLabel(role: string): string {
    return role === 'owner'
      ? this.i18n.t('personal.household.role.owner')
      : this.i18n.t('personal.household.role.member');
  }

  toggleRemember(event: Event): void {
    const on = (event.target as HTMLInputElement).checked;
    this.remember.set(on);
    this.profileSwitch.setRememberProfile(on);
  }

  async select(p: ProfileCard): Promise<void> {
    if (p.is_me) {
      this.selectedId.set(p.user_id);
      this.profileSwitch.markContinueAsMe(this.remember());
      if (p.pin_enabled) {
        await this.openSelfPinIfNeeded(p);
        return;
      }
      void this.enterApp();
      return;
    }

    if (p.pin_enabled && this.trustedDevice.getToken(p.user_id)) {
      this.openPinModal(p, 'other');
      return;
    }
    this.switchTarget.set(p);
  }

  private async openSelfPinIfNeeded(p: ProfileCard): Promise<void> {
    try {
      const status = await firstValueFrom(this.securityApi.getPinStatus());
      this.pinStatusCache = status;
      if (!status.enabled || !status.require_on_select) {
        void this.enterApp();
        return;
      }
      if (status.locked) {
        this.openPinModal(p, 'self');
        this.pinLocked.set(true);
        return;
      }
      this.openPinModal(p, 'self');
    } catch {
      void this.enterApp();
    }
  }

  private openPinModal(p: ProfileCard, mode: PinModalMode): void {
    this.clearPinFields();
    this.pinMode.set(mode);
    this.pinTarget.set(p);
    this.pinLocked.set(false);
    this.pinError.set(null);
  }

  cancelSwitch(): void {
    this.switchTarget.set(null);
    this.switching.set(false);
  }

  cancelPin(): void {
    this.pinTarget.set(null);
    this.clearPinFields();
    this.pinStatusCache = null;
  }

  appendPinDigit(digit: string): void {
    if (this.pinSubmitting() || this.pinLocked()) return;
    if (this.pinValue.length >= 6) return;
    this.pinValue += digit;
  }

  backspacePin(): void {
    if (this.pinSubmitting() || this.pinLocked()) return;
    this.pinValue = this.pinValue.slice(0, -1);
  }

  async submitPin(): Promise<void> {
    const target = this.pinTarget();
    if (!target || this.pinSubmitting() || this.pinLocked()) return;
    const pin = this.pinValue.trim();
    if (pin.length < 4) {
      this.pinError.set(this.i18n.t('personal.profiles.pinInvalid'));
      return;
    }

    this.pinSubmitting.set(true);
    this.pinError.set(null);

    try {
      if (this.pinMode() === 'self') {
        const deviceToken = this.trustedDevice.getToken(target.user_id);
        await firstValueFrom(this.securityApi.verifyPin(pin, deviceToken));
        this.clearPinFields();
        this.pinTarget.set(null);
        void this.enterApp();
      } else {
        const deviceToken = this.trustedDevice.getToken(target.user_id);
        if (!deviceToken) {
          this.pinError.set(this.i18n.t('personal.profiles.pinDeviceRequired'));
          return;
        }
        const result = await this.profileSwitch.tryPinUnlockSwitch(target.user_id, pin, deviceToken);
        this.clearPinFields();
        if (result === 'ok') {
          this.pinTarget.set(null);
          this.leaving.set(true);
          await this.router.navigateByUrl('/discover');
          return;
        }
        if (result === 'password_required') {
          this.pinTarget.set(null);
          this.switchTarget.set(target);
          return;
        }
        this.pinError.set(this.i18n.t('personal.profiles.pinIncorrect'));
      }
    } catch (err: unknown) {
      const code = SecurityApiService.errorCode(err);
      if (code === 'pin_locked') {
        this.pinLocked.set(true);
        this.pinError.set(null);
      } else if (code === 'pin_incorrect') {
        this.pinError.set(this.i18n.t('personal.profiles.pinIncorrect'));
      } else {
        this.pinError.set(
          SecurityApiService.errorMessage(err) ?? this.i18n.t('common.actionFailed'),
        );
      }
    } finally {
      this.pinSubmitting.set(false);
      this.clearPinValueOnly();
    }
  }

  forgotPin(): void {
    const target = this.pinTarget();
    if (!target) return;
    this.cancelPin();
    if (target.is_me) {
      void this.router.navigate(['/settings'], { queryParams: { tab: 'security' } });
      return;
    }
    this.switchTarget.set(target);
  }

  async confirmSwitch(): Promise<void> {
    const target = this.switchTarget();
    if (!target || this.switching()) return;
    this.switching.set(true);
    try {
      await this.profileSwitch.prepareAndSwitch(target.user_id);
    } catch {
      this.error.set(this.i18n.t('common.actionFailed'));
      this.switching.set(false);
      this.switchTarget.set(null);
    }
  }

  private clearPinValueOnly(): void {
    this.pinValue = '';
  }

  private clearPinFields(): void {
    this.pinValue = '';
    this.pinVisible.set(false);
    this.pinError.set(null);
    this.pinLocked.set(false);
    this.pinSubmitting.set(false);
  }

  private async enterApp(): Promise<void> {
    this.leaving.set(true);
    try {
      this.favorites?.refreshIds?.();
      this.history?.reload?.();
    } catch {
      /* optional */
    }
    const delay =
      typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 0
        : 280;
    await new Promise((r) => setTimeout(r, delay));
    await this.router.navigateByUrl(this.returnUrl || '/discover');
  }

  exit(): void {
    this.profileSwitch.switchToLoginHint(null);
  }
}
