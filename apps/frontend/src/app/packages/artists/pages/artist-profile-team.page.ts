import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistAssignment, ArtistTeamMember } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-artist-profile-team',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="artist-profile-team-page">
      <a [routerLink]="['/artist-profiles', artistId]">&larr; Back to profile</a>
      <h1>{{ 'artists.team.title' | t:lang() }}</h1>

      <section class="assignments">
        <h2>Manager Assignments</h2>
        <form [formGroup]="assignForm" (ngSubmit)="assignManager()">
          <input formControlName="user_id" type="number" placeholder="User id" class="input" />
          <input formControlName="role" placeholder="Role (default: manager)" class="input" />
          <button type="submit" class="btn btn--primary" [disabled]="assignForm.invalid">
            Assign Manager
          </button>
        </form>

        @if (assignments.length === 0) {
          <p>No manager assignments yet.</p>
        } @else {
          <ul>
            @for (a of assignments; track a.id) {
              <li>
                User #{{ a.user_id }} — {{ a.role }} — <span class="badge" [class]="'badge--' + a.status">{{ a.status }}</span>
                @if (a.status === 'active') {
                  <button class="btn btn--small btn--danger" (click)="endAssignment(a.id)">End</button>
                }
              </li>
            }
          </ul>
        }
      </section>

      <section class="team">
        <h2>Team Members</h2>
        <form [formGroup]="teamForm" (ngSubmit)="addTeamMember()">
          <input formControlName="user_id" type="number" placeholder="User id" class="input" />
          <input formControlName="team_role" placeholder="Team role (e.g. producer)" class="input" />
          <button type="submit" class="btn btn--primary" [disabled]="teamForm.invalid">
            Add Team Member
          </button>
        </form>

        @if (team.length === 0) {
          <p>No team members yet.</p>
        } @else {
          <ul>
            @for (m of team; track m.id) {
              <li>
                User #{{ m.user_id }} — {{ m.team_role }} — <span class="badge" [class]="'badge--' + m.status">{{ m.status }}</span>
                @if (m.status === 'active') {
                  <button class="btn btn--small btn--danger" (click)="removeTeamMember(m.id)">Remove</button>
                }
              </li>
            }
          </ul>
        }
      </section>

      @if (error) {
        <p class="error">{{ error }}</p>
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

  assignForm = this.fb.group({
    user_id: [null as number | null, [Validators.required]],
    role: ['manager'],
  });

  teamForm = this.fb.group({
    user_id: [null as number | null, [Validators.required]],
    team_role: ['', [Validators.required]],
  });

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  get artistId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.loadAssignments();
    this.loadTeam();
  }

  loadAssignments(): void {
    this.api.listAssignments(this.orgId, this.artistId).subscribe({
      next: (items) => (this.assignments = items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading assignments'),
    });
  }

  loadTeam(): void {
    this.api.listTeam(this.orgId, this.artistId).subscribe({
      next: (items) => (this.team = items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading team'),
    });
  }

  assignManager(): void {
    if (this.assignForm.invalid) return;
    const value = this.assignForm.value;
    this.api
      .assignManager(this.orgId, this.artistId, Number(value.user_id), value.role || 'manager')
      .subscribe({
        next: () => {
          this.assignForm.reset({ role: 'manager' });
          this.loadAssignments();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error assigning manager'),
      });
  }

  endAssignment(assignmentId: number): void {
    this.api.endAssignment(this.orgId, this.artistId, assignmentId).subscribe({
      next: () => this.loadAssignments(),
      error: (e) => (this.error = e.error?.message ?? 'Error ending assignment'),
    });
  }

  addTeamMember(): void {
    if (this.teamForm.invalid) return;
    const value = this.teamForm.value;
    this.api
      .addTeamMember(this.orgId, this.artistId, Number(value.user_id), value.team_role!)
      .subscribe({
        next: () => {
          this.teamForm.reset();
          this.loadTeam();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error adding team member'),
      });
  }

  removeTeamMember(memberId: number): void {
    this.api.removeTeamMember(this.orgId, this.artistId, memberId).subscribe({
      next: () => this.loadTeam(),
      error: (e) => (this.error = e.error?.message ?? 'Error removing team member'),
    });
  }
}
