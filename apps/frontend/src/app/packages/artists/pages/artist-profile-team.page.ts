import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistAssignment, ArtistTeamMember } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-profile-team',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-profile-team-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a [routerLink]="['/artist-profiles', artistId]" class="back-link">
          {{ 'artists.team.back' | t:lang() }}
        </a>

        <app-enterprise-page-header [title]="'artists.team.title' | t:lang()" />

        <app-enterprise-section-card [title]="'artists.team.assignments' | t:lang()">
          <form [formGroup]="assignForm" (ngSubmit)="assignManager()" class="form-grid">
            <app-enterprise-form-field [label]="'artists.team.userId' | t:lang()" [required]="true">
              <input formControlName="user_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'artists.team.role' | t:lang()">
              <input formControlName="role" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="assignForm.invalid">
                {{ 'artists.team.assign' | t:lang() }}
              </button>
            </div>
          </form>

          @if (assignments.length === 0) {
            <p class="muted">{{ 'artists.team.noAssignments' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (a of assignments; track a.id) {
                <li>
                  User #{{ a.user_id }} — {{ a.role }} —
                  <app-enterprise-status-badge [status]="a.status" />
                  @if (a.status === 'active') {
                    <button class="btn btn--small btn--danger" (click)="endAssignment(a.id)">
                      {{ 'artists.team.end' | t:lang() }}
                    </button>
                  }
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'artists.team.members' | t:lang()">
          <form [formGroup]="teamForm" (ngSubmit)="addTeamMember()" class="form-grid">
            <app-enterprise-form-field [label]="'artists.team.userId' | t:lang()" [required]="true">
              <input formControlName="user_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'artists.team.teamRole' | t:lang()" [required]="true">
              <input formControlName="team_role" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="teamForm.invalid">
                {{ 'artists.team.addMember' | t:lang() }}
              </button>
            </div>
          </form>

          @if (team.length === 0) {
            <p class="muted">{{ 'artists.team.noMembers' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (m of team; track m.id) {
                <li>
                  User #{{ m.user_id }} — {{ m.team_role }} —
                  <app-enterprise-status-badge [status]="m.status" />
                  @if (m.status === 'active') {
                    <button class="btn btn--small btn--danger" (click)="removeTeamMember(m.id)">
                      {{ 'artists.team.remove' | t:lang() }}
                    </button>
                  }
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" />
        }
      }
    </div>
  `,
})
export class ArtistProfileTeamPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ArtistsApiService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  assignments: ArtistAssignment[] = [];
  team: ArtistTeamMember[] = [];
  error: string | null = null;
  orgId: number | null = null;

  assignForm = this.fb.group({
    user_id: [null as number | null, [Validators.required]],
    role: ['manager'],
  });

  teamForm = this.fb.group({
    user_id: [null as number | null, [Validators.required]],
    team_role: ['', [Validators.required]],
  });

  get artistId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) {
      this.loadAssignments();
      this.loadTeam();
    }
  }

  loadAssignments(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listAssignments(orgId, this.artistId).subscribe({
      next: (items) => (this.assignments = items),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  loadTeam(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listTeam(orgId, this.artistId).subscribe({
      next: (items) => (this.team = items),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  assignManager(): void {
    const orgId = this.orgId;
    if (!orgId || this.assignForm.invalid) return;
    const value = this.assignForm.value;
    this.api
      .assignManager(orgId, this.artistId, Number(value.user_id), value.role || 'manager')
      .subscribe({
        next: () => {
          this.assignForm.reset({ role: 'manager' });
          this.loadAssignments();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  endAssignment(assignmentId: number): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.endAssignment(orgId, this.artistId, assignmentId).subscribe({
      next: () => this.loadAssignments(),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  addTeamMember(): void {
    const orgId = this.orgId;
    if (!orgId || this.teamForm.invalid) return;
    const value = this.teamForm.value;
    this.api
      .addTeamMember(orgId, this.artistId, Number(value.user_id), value.team_role!)
      .subscribe({
        next: () => {
          this.teamForm.reset();
          this.loadTeam();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  removeTeamMember(memberId: number): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.removeTeamMember(orgId, this.artistId, memberId).subscribe({
      next: () => this.loadTeam(),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }
}
