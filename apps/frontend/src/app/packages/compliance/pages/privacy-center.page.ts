import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ComplianceApiService } from '../services/compliance-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { ConsentRecord, DataRequest } from '../models/compliance.models';

@Component({
  selector: 'app-privacy-center',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="privacy-center">
      <h1>Privacy Center</h1>
      <p class="subtitle">Manage your consent and data subject requests.</p>

      <section>
        <h2>My Consent Records</h2>
        @if (loading) { <p>Loading…</p> }
        @else if (consents.length === 0) { <p>No consent records.</p> }
        @else {
          <ul>
            @for (c of consents; track c.id) {
              <li>Consent #{{ c.id }} — {{ c.status }}</li>
            }
          </ul>
        }
      </section>

      <section>
        <h2>Submit Data Request</h2>
        <form [formGroup]="dsrForm" (ngSubmit)="submitDsr()">
          <select formControlName="request_type" class="input">
            <option value="access">Access</option>
            <option value="export">Export</option>
            <option value="correction">Correction</option>
            <option value="deletion">Deletion</option>
          </select>
          <input formControlName="reason" placeholder="Reason (optional)" class="input" />
          <button type="submit" class="btn btn--primary" [disabled]="dsrForm.invalid">Submit</button>
        </form>
        @if (dsrSuccess) { <p class="success">Request submitted (ID: {{ dsrSuccess.id }})</p> }
      </section>

      @if (error) { <p class="error">{{ error }}</p> }
    </div>
  `,
})
export class PrivacyCenterPage implements OnInit {
  private api = inject(ComplianceApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  consents: ConsentRecord[] = [];
  loading = false;
  error: string | null = null;
  dsrSuccess: DataRequest | null = null;

  dsrForm = this.fb.group({ request_type: ['access', Validators.required], reason: [''] });

  ngOnInit(): void { this.load(); }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    this.loading = true;
    this.api.myConsentRecords(orgId).subscribe({
      next: (r) => { this.consents = r; this.loading = false; },
      error: (e) => { this.error = e?.error?.message || 'Failed to load'; this.loading = false; },
    });
  }

  submitDsr(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId || this.dsrForm.invalid) { this.error = 'Select an organization'; return; }
    const v = this.dsrForm.value;
    this.api.submitDsr(orgId, { request_type: v.request_type!, reason: v.reason || undefined }).subscribe({
      next: (r) => { this.dsrSuccess = r; this.error = null; },
      error: (e) => { this.error = e?.error?.message || 'Submit failed'; },
    });
  }
}
