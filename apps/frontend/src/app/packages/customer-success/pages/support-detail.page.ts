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
      @if (error) { <p class="error">{{ error }}</p> }
      @if (caseData) {
        <h1>{{ $any(caseData).subject }}</h1>
        <p>{{ $any(caseData).status }} / {{ $any(caseData).priority }}</p>
        <button type="button" (click)="resolve()">Resolve</button>
        <button type="button" (click)="close()">Close</button>
        <h2>Messages</h2>
        <ul>
          @for (m of messages; track $index) {
            <li [class.internal]="$any(m).is_internal">
              {{ $any(m).is_internal ? '[internal] ' : '' }}{{ $any(m).body }}
            </li>
          }
        </ul>
        <input [(ngModel)]="body" placeholder="message" />
        <button type="button" (click)="send(false)">Send</button>
        <button type="button" (click)="send(true)">Internal note</button>
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

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.api.getCase(this.orgId, this.id).subscribe({
      next: (c) => (this.caseData = c),
      error: (e) => (this.error = e?.error?.detail?.message || 'Denied'),
    });
    this.api.listMessages(this.orgId, this.id, true).subscribe({
      next: (m) => (this.messages = m || []),
    });
  }

  send(internal: boolean): void {
    if (!this.orgId || !this.body) return;
    const req = internal
      ? this.api.addInternalNote(this.orgId, this.id, this.body)
      : this.api.addMessage(this.orgId, this.id, this.body);
    req.subscribe({
      next: () => {
        this.body = '';
        this.reload();
      },
      error: (e) => (this.error = e?.error?.detail?.message || 'Send failed'),
    });
  }

  resolve(): void {
    if (!this.orgId) return;
    this.api.resolve(this.orgId, this.id).subscribe({ next: () => this.reload() });
  }

  close(): void {
    if (!this.orgId) return;
    this.api.close(this.orgId, this.id).subscribe({ next: () => this.reload() });
  }
}
