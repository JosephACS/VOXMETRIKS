import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-support-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page">
      <h1>Support</h1>
      <p class="subtitle">Organization-scoped tickets. Internal notes require staff permission.</p>
      <nav class="subnav"><a routerLink="/customer-success">CS</a> | <a routerLink="/support">Support</a></nav>
      @if (!orgId) {
        <p class="error">Select an organization context.</p>
      } @else {
        <section>
          <input [(ngModel)]="subject" placeholder="subject" />
          <button type="button" (click)="create()" [disabled]="busy || !subject">Create ticket</button>
        </section>
        @if (loading) { <p>Loading…</p> }
        @else if (error) { <p class="error">{{ error }}</p> }
        @else if (!cases.length) { <p class="empty-state">No support cases yet.</p> }
        @else {
          <ul>
            @for (c of cases; track $index) {
              <li>
                <a [routerLink]="['/support', $any(c).id]">{{ $any(c).subject }}</a>
                — {{ $any(c).status }} / {{ $any(c).priority }}
              </li>
            }
          </ul>
        }
      }
    </div>
  `,
})
export class SupportListPage implements OnInit {
  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);
  orgId: number | null = null;
  cases: unknown[] = [];
  subject = '';
  error = '';
  loading = false;
  busy = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (this.orgId) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = '';
    this.api.listCases(this.orgId).subscribe({
      next: (c) => {
        this.cases = c || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Failed to load cases';
        this.loading = false;
      },
    });
  }

  create(): void {
    if (!this.orgId || !this.subject) return;
    this.busy = true;
    this.api.createCase(this.orgId, this.subject).subscribe({
      next: () => {
        this.subject = '';
        this.busy = false;
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Create failed';
        this.busy = false;
      },
    });
  }
}
