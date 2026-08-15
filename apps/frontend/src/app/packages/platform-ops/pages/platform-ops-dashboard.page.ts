import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import {
  PLATFORM_OPS_QUEUE_PATHS,
  PlatformOpsOverview,
  PlatformOpsQueue,
  PlatformOpsQueueCode,
} from '../models/platform-ops.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-platform-ops-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-ops-page" data-testid="platform-ops-dashboard">
      <app-enterprise-page-header
        [title]="'platformOps.overview.title' | t: lang()"
        [subtitle]="'platformOps.overview.subtitle' | t: lang()"
      >
        <a routerLink="/platform-ops/system" class="btn btn--ghost" data-testid="platform-ops-system-link">
          {{ 'platformOps.overview.openSystem' | t: lang() }}
        </a>
      </app-enterprise-page-header>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="5" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (overview(); as ov) {
        <app-enterprise-section-card [title]="'platformOps.overview.health' | t: lang()">
          <p class="health-line" data-testid="platform-ops-health">
            <strong>{{ healthLabel(ov.health) }}</strong>
            <span>{{ 'platformOps.overview.healthHint.' + ov.health | t: lang() }}</span>
          </p>
        </app-enterprise-section-card>

        @if (ov.next_queue) {
          <app-enterprise-section-card
            [title]="'platformOps.overview.nextAction' | t: lang()"
            data-testid="platform-ops-next-queue"
          >
            <p>
              {{ queueLabel(ov.next_queue) }}
              —
              {{ 'platformOps.overview.nextActionBody' | t: lang() }}
            </p>
            <a
              class="btn btn--primary"
              [routerLink]="queuePath(ov.next_queue)"
              [attr.data-testid]="'platform-ops-next-' + ov.next_queue"
            >
              {{ 'platformOps.overview.openQueue' | t: lang() }}
            </a>
          </app-enterprise-section-card>
        } @else {
          <app-enterprise-empty-state
            [title]="'platformOps.overview.allClearTitle' | t: lang()"
            [description]="'platformOps.overview.allClearBody' | t: lang()"
          />
        }

        <div class="queue-grid" data-testid="platform-ops-queues">
          @for (q of ov.queues; track q.code) {
            <a
              class="queue-card"
              [class.queue-card--attention]="q.severity === 'attention'"
              [class.queue-card--critical]="q.severity === 'critical'"
              [class.queue-card--unavailable]="q.availability === 'unavailable'"
              [routerLink]="queuePath(q.code)"
              [attr.data-testid]="'platform-ops-queue-' + q.code"
            >
              <h3>{{ queueLabel(q.code) }}</h3>
              <p class="queue-count">
                @if (q.availability === 'unavailable') {
                  {{ 'platformOps.overview.unavailable' | t: lang() }}
                } @else {
                  {{ q.count ?? 0 }}
                }
              </p>
              <p class="queue-meta">{{ severityLabel(q) }}</p>
            </a>
          }
        </div>
      }
    </div>
  `,
  styles: `
    .health-line {
      display: flex;
      gap: 0.75rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .queue-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
      gap: 0.85rem;
      margin-top: 1rem;
    }
    .queue-card {
      display: block;
      padding: 1rem;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: rgba(255, 255, 255, 0.03);
      color: inherit;
      text-decoration: none;
      min-height: 7rem;
    }
    .queue-card:hover,
    .queue-card:focus-visible {
      border-color: rgba(147, 197, 253, 0.55);
      outline: none;
    }
    .queue-card--attention {
      border-color: rgba(240, 195, 106, 0.45);
    }
    .queue-card--critical {
      border-color: rgba(248, 113, 113, 0.5);
    }
    .queue-card--unavailable {
      opacity: 0.72;
    }
    .queue-card h3 {
      margin: 0 0 0.5rem;
      font-size: 0.95rem;
      font-weight: 600;
    }
    .queue-count {
      margin: 0;
      font-size: 1.6rem;
      font-weight: 700;
    }
    .queue-meta {
      margin: 0.35rem 0 0;
      font-size: 0.8rem;
      opacity: 0.7;
    }
    @media (max-width: 480px) {
      .queue-grid {
        grid-template-columns: 1fr;
      }
    }
  `,
})
export class PlatformOpsDashboardPage implements OnInit {
  private readonly api = inject(PlatformOpsApiService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly overview = signal<PlatformOpsOverview | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.getOverview().subscribe({
      next: (ov) => {
        this.overview.set(ov);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(
          err?.error?.detail?.message ||
            err?.error?.message ||
            this.i18n.t('platformOps.overview.loadFailed'),
        );
        this.loading.set(false);
      },
    });
  }

  queuePath(code: PlatformOpsQueueCode): string {
    return PLATFORM_OPS_QUEUE_PATHS[code];
  }

  queueLabel(code: PlatformOpsQueueCode): string {
    return this.i18n.t(`platformOps.overview.queue.${code}`);
  }

  healthLabel(health: string): string {
    return this.i18n.t(`platformOps.overview.healthLabel.${health}`);
  }

  severityLabel(q: PlatformOpsQueue): string {
    if (q.availability === 'unavailable') {
      return this.i18n.t('platformOps.overview.unavailable');
    }
    return this.i18n.t(`platformOps.overview.severity.${q.severity}`);
  }
}
