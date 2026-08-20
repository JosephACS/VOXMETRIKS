import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import { OperationalIncident } from '../models/platform-ops.models';
import { I18nService } from '../../../core/services/i18n.service';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-platform-ops-incidents-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-ops-page" data-testid="platform-ops-incidents">
      <a routerLink="/platform-ops" class="back-link">{{ 'platformOps.incidents.back' | t: lang() }}</a>
      <app-enterprise-page-header
        [title]="'platformOps.incidents.title' | t: lang()"
        [subtitle]="'platformOps.incidents.subtitle' | t: lang()"
      />

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (feedback()) {
        <p class="success" role="status">{{ feedback() }}</p>
      }

      <app-enterprise-section-card [title]="'platformOps.incidents.create' | t: lang()">
        <form class="form-grid" (ngSubmit)="create()">
          <app-enterprise-form-field [label]="'platformOps.incidents.fieldTitle' | t: lang()" [required]="true">
            <input class="input" [(ngModel)]="title" name="title" required />
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'platformOps.incidents.severity' | t: lang()" [required]="true">
            <select class="input" [(ngModel)]="severity" name="severity">
              <option value="low">{{ 'platformOps.incidents.sev.low' | t: lang() }}</option>
              <option value="medium">{{ 'platformOps.incidents.sev.medium' | t: lang() }}</option>
              <option value="high">{{ 'platformOps.incidents.sev.high' | t: lang() }}</option>
              <option value="critical">{{ 'platformOps.incidents.sev.critical' | t: lang() }}</option>
            </select>
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'platformOps.incidents.description' | t: lang()" [required]="true">
            <textarea class="input" [(ngModel)]="description" name="description" rows="3" required></textarea>
          </app-enterprise-form-field>
          <div class="form-grid__actions">
            <button type="submit" class="btn btn--primary" [disabled]="busy() || !title.trim() || !description.trim()">
              {{ 'platformOps.incidents.create' | t: lang() }}
            </button>
          </div>
        </form>
      </app-enterprise-section-card>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (!items().length) {
        <app-enterprise-empty-state
          [title]="'platformOps.incidents.emptyTitle' | t: lang()"
          [description]="'platformOps.incidents.emptyBody' | t: lang()"
        />
      } @else {
        <app-enterprise-data-table>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'platformOps.incidents.fieldTitle' | t: lang() }}</th>
                <th>{{ 'platformOps.incidents.severity' | t: lang() }}</th>
                <th>{{ 'common.status' | t: lang() }}</th>
                <th>{{ 'common.actions' | t: lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (inc of items(); track inc.id) {
                <tr>
                  <td>
                    <strong>{{ inc.title }}</strong>
                    <div class="muted">{{ inc.description }}</div>
                  </td>
                  <td><app-enterprise-status-badge [status]="inc.severity" /></td>
                  <td><app-enterprise-status-badge [status]="inc.status" /></td>
                  <td>
                    @if (inc.status === 'open' || inc.status === 'investigating') {
                      <button
                        type="button"
                        class="btn btn--secondary btn--sm"
                        [disabled]="busy()"
                        (click)="resolve(inc)"
                      >
                        {{ 'platformOps.incidents.resolve' | t: lang() }}
                      </button>
                    } @else {
                      <span class="muted">{{ 'common.notAvailable' | t: lang() }}</span>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </app-enterprise-data-table>
      }
    </div>
  `,
})
export class PlatformOpsIncidentsPage implements OnInit {
  private readonly api = inject(PlatformOpsApiService);
  private readonly i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly feedback = signal<string | null>(null);
  readonly items = signal<OperationalIncident[]>([]);

  title = '';
  severity: 'low' | 'medium' | 'high' | 'critical' = 'medium';
  description = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listIncidents().subscribe({
      next: (rows) => {
        this.items.set(rows || []);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(userFacingHttpError(this.i18n, err));
        this.loading.set(false);
      },
    });
  }

  create(): void {
    if (this.busy() || !this.title.trim() || !this.description.trim()) return;
    this.busy.set(true);
    this.feedback.set(null);
    this.api
      .createIncident({
        title: this.title.trim(),
        severity: this.severity,
        description: this.description.trim(),
      })
      .subscribe({
        next: () => {
          this.busy.set(false);
          this.title = '';
          this.description = '';
          this.severity = 'medium';
          this.feedback.set(this.i18n.t('platformOps.incidents.created'));
          this.load();
        },
        error: (err) => {
          this.busy.set(false);
          this.error.set(userFacingHttpError(this.i18n, err));
        },
      });
  }

  resolve(inc: OperationalIncident): void {
    if (this.busy()) return;
    this.busy.set(true);
    this.feedback.set(null);
    this.api.resolveIncident(inc.id).subscribe({
      next: () => {
        this.busy.set(false);
        this.feedback.set(this.i18n.t('platformOps.incidents.resolved'));
        this.load();
      },
      error: (err) => {
        this.busy.set(false);
        this.error.set(userFacingHttpError(this.i18n, err));
      },
    });
  }
}
