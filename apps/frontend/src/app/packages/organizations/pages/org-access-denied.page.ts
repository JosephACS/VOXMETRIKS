import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs/operators';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

export type AccessDeniedReason =
  | 'permission'
  | 'membership'
  | 'platform'
  | 'artist'
  | 'plan'
  | 'default';

function normalizeReason(raw: string | null | undefined): AccessDeniedReason {
  switch ((raw || '').toLowerCase()) {
    case 'permission':
    case 'org_permission':
      return 'permission';
    case 'membership':
    case 'org_membership':
    case 'organization':
      return 'membership';
    case 'platform':
    case 'platform_admin':
      return 'platform';
    case 'artist':
    case 'artist_permission':
      return 'artist';
    case 'plan':
    case 'tier':
      return 'plan';
    default:
      return 'default';
  }
}

@Component({
  selector: 'app-org-access-denied-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-access-denied">
      <h1>{{ titleKey() | t: lang() }}</h1>
      <p class="lede">{{ bodyKey() | t: lang() }}</p>
      <p class="org-muted">{{ hintKey() | t: lang() }}</p>
      <div class="org-actions">
        @if (reason() === 'plan') {
          <a class="org-btn" routerLink="/subscriptions/select-plan">
            {{ 'organizations.accessDenied.ctaPlan' | t: lang() }}
          </a>
          <a class="org-btn org-btn--ghost" routerLink="/organizations">
            {{ 'organizations.accessDenied.ctaOrg' | t: lang() }}
          </a>
        } @else if (reason() === 'platform') {
          <a class="org-btn" routerLink="/discover">
            {{ 'organizations.accessDenied.ctaDiscover' | t: lang() }}
          </a>
          <a class="org-btn org-btn--ghost" routerLink="/settings">
            {{ 'organizations.accessDenied.ctaSettings' | t: lang() }}
          </a>
        } @else if (reason() === 'artist') {
          <a class="org-btn" routerLink="/artist-space">
            {{ 'organizations.accessDenied.ctaArtist' | t: lang() }}
          </a>
          <a class="org-btn org-btn--ghost" routerLink="/discover">
            {{ 'organizations.accessDenied.ctaDiscover' | t: lang() }}
          </a>
        } @else if (reason() === 'membership') {
          <a class="org-btn" routerLink="/organizations">
            {{ 'organizations.accessDenied.ctaOrg' | t: lang() }}
          </a>
          <a class="org-btn org-btn--ghost" routerLink="/invitations/accept">
            {{ 'organizations.accessDenied.ctaInvite' | t: lang() }}
          </a>
        } @else {
          <a class="org-btn" routerLink="/organizations">
            {{ 'organizations.accessDenied.ctaOrg' | t: lang() }}
          </a>
          <a class="org-btn org-btn--ghost" routerLink="/discover">
            {{ 'organizations.accessDenied.ctaDiscover' | t: lang() }}
          </a>
        }
      </div>
    </section>
  `,
})
export class OrgAccessDeniedPageComponent {
  private readonly i18n = inject(I18nService);
  private readonly route = inject(ActivatedRoute);
  readonly lang = this.i18n.lang;

  private readonly reasonParam = toSignal(
    this.route.queryParamMap.pipe(map((q) => q.get('reason'))),
    { initialValue: this.route.snapshot.queryParamMap.get('reason') },
  );

  readonly reason = computed(() => normalizeReason(this.reasonParam()));

  titleKey(): string {
    const r = this.reason();
    if (r === 'plan') return 'organizations.accessDenied.planTitle';
    if (r === 'platform') return 'organizations.accessDenied.platformTitle';
    if (r === 'artist') return 'organizations.accessDenied.artistTitle';
    if (r === 'membership') return 'organizations.accessDenied.membershipTitle';
    if (r === 'permission') return 'organizations.accessDenied.permissionTitle';
    return 'organizations.accessDenied.title';
  }

  bodyKey(): string {
    const r = this.reason();
    if (r === 'plan') return 'organizations.accessDenied.planBody';
    if (r === 'platform') return 'organizations.accessDenied.platformBody';
    if (r === 'artist') return 'organizations.accessDenied.artistBody';
    if (r === 'membership') return 'organizations.accessDenied.membershipBody';
    if (r === 'permission') return 'organizations.accessDenied.permissionBody';
    return 'organizations.accessDenied.body';
  }

  hintKey(): string {
    const r = this.reason();
    if (r === 'plan') return 'organizations.accessDenied.planHint';
    if (r === 'platform') return 'organizations.accessDenied.platformHint';
    if (r === 'artist') return 'organizations.accessDenied.artistHint';
    if (r === 'membership') return 'organizations.accessDenied.membershipHint';
    if (r === 'permission') return 'organizations.accessDenied.permissionHint';
    return 'organizations.accessDenied.hint';
  }
}
