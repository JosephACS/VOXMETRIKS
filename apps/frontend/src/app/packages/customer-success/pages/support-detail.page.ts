import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-support-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page">
      <p><a routerLink="/support">← Support</a></p>
      @if (loading) {
        <p>Loading…</p>
      } @else if (error && !caseData) {
        <p class="error">{{ error }}</p>
      } @else if (!caseData) {
        <p class="empty-state">Case not found.</p>
      } @else {
        @if (error) {
          <p class="error">{{ error }}</p>
        }
        @if (success) {
          <p class="success">{{ success }}</p>
        }
        <h1>{{ $any(caseData).subject || 'No disponible' }}</h1>
        <p>
          <span class="badge">{{ $any(caseData).status || 'No disponible' }}</span>
          /
          {{ $any(caseData).priority || 'No disponible' }}
        </p>
        <div class="actions">
          <button type="button" (click)="resolve()" [disabled]="busy">Resolve</button>
          <button type="button" (click)="closeCase()" [disabled]="busy">Close</button>
        </div>
        <h2>Messages</h2>
        @if (messages.length === 0) {
          <p class="empty-state">No messages yet.</p>
        } @else {
          <ul>
            @for (m of messages; track $index) {
              <li [class.internal]="$any(m).is_internal">
                {{ $any(m).is_internal ? '[internal] ' : '' }}{{ $any(m).body || 'No disponible' }}
              </li>
            }
          </ul>
        }
        <div class="form-actions">
          <input [(ngModel)]="body" placeholder="message" />
          <button type="button" (click)="send(false)" [disabled]="busy || !body.trim()">Send</button>
          <button type="button" (click)="send(true)" [disabled]="busy || !body.trim()">Internal note</button>
        </div>
      }
    </div>
  `,
})
export class SupportDetailPage implements OnInit {
  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  orgId: number | null = null;
  id = 0;
  caseData: unknown = null;
  messages: unknown[] = [];
  body = '';
  error = '';
  success = '';
  loading = false;
  busy = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
    else this.error = 'Select an organization context.';
  }

  reload(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.loading = true;
    this.error = '';
    this.api.getCase(orgId, this.id).subscribe({
      next: (c) => {
        this.caseData = c;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Denied or not found';
        this.loading = false;
      },
    });
    this.api.listMessages(orgId, this.id, true).subscribe({
      next: (m) => (this.messages = m || []),
      error: () => {
        /* keep case visible even if messages fail */
      },
    });
  }

  send(internal: boolean): void {
    const orgId = this.orgId;
    if (orgId == null || !this.body.trim()) return;
    this.busy = true;
    this.error = '';
    const req = internal
      ? this.api.addInternalNote(orgId, this.id, this.body)
      : this.api.addMessage(orgId, this.id, this.body);
    req.subscribe({
      next: () => {
        this.body = '';
        this.busy = false;
        this.success = internal ? 'Internal note added.' : 'Message sent.';
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Send failed';
        this.busy = false;
      },
    });
  }

  resolve(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.error = '';
    this.api.resolve(orgId, this.id).subscribe({
      next: () => {
        this.busy = false;
        this.success = 'Case resolved.';
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Resolve failed';
        this.busy = false;
      },
    });
  }

  closeCase(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    if (!confirm('Close this support case?')) return;
    this.busy = true;
    this.error = '';
    this.api.close(orgId, this.id).subscribe({
      next: () => {
        this.busy = false;
        this.success = 'Case closed.';
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Close failed';
        this.busy = false;
      },
    });
  }
}
