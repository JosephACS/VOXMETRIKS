import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { BillingProfile } from '../models/billing.models';

@Component({
  selector: 'app-billing-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="billing-profile-page">
      <h1>Billing Profile</h1>
      @if (profile) {
        <div class="profile-card">
          <div class="field"><label>Currency</label><span>{{ profile.default_currency }}</span></div>
          <div class="field"><label>Legal Name</label><span>{{ profile.legal_name ?? '—' }}</span></div>
          <div class="field"><label>Tax ID</label><span>{{ profile.tax_id ?? '—' }}</span></div>
          <div class="field"><label>Email</label><span>{{ profile.email ?? '—' }}</span></div>
          <div class="field"><label>Status</label>
            <span class="badge" [class]="'badge--' + profile.status">{{ profile.status }}</span>
          </div>
        </div>
        <button class="btn btn--secondary" (click)="editMode = !editMode">Edit</button>
        @if (editMode) {
          <form [formGroup]="editForm" (ngSubmit)="saveProfile()" class="mt-4">
            <input formControlName="legal_name" placeholder="Legal name" class="input">
            <input formControlName="tax_id" placeholder="Tax ID" class="input">
            <input formControlName="billing_address" placeholder="Address" class="input">
            <input formControlName="email" placeholder="Email" class="input">
            <button type="submit" class="btn btn--primary">Save</button>
          </form>
        }
      } @else {
        <p>No billing profile. Create one to start invoicing.</p>
        <form [formGroup]="createForm" (ngSubmit)="createProfile()" class="create-form">
          <input formControlName="default_currency" placeholder="Currency (e.g. USD)" maxlength="3" class="input">
          <input formControlName="legal_name" placeholder="Legal name" class="input">
          <input formControlName="email" placeholder="Billing email" class="input">
          <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
            Create Billing Profile
          </button>
        </form>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class BillingProfilePage implements OnInit {
  private api = inject(BillingApiService);
  private fb = inject(FormBuilder);

  profile: BillingProfile | null = null;
  error: string | null = null;
  editMode = false;

  orgId = 1; // In production: from org context service

  createForm = this.fb.group({
    default_currency: ['', [Validators.required, Validators.maxLength(3), Validators.minLength(3)]],
    legal_name: [''],
    email: [''],
  });

  editForm = this.fb.group({
    legal_name: [''],
    tax_id: [''],
    billing_address: [''],
    email: [''],
  });

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    this.api.getProfile(this.orgId).subscribe({
      next: (p) => (this.profile = p),
      error: (e) => {
        if (e.status === 404) this.profile = null;
        else this.error = e.error?.message ?? 'Error loading profile';
      },
    });
  }

  createProfile(): void {
    if (this.createForm.invalid) return;
    this.api.createProfile(this.orgId, this.createForm.value as Partial<BillingProfile>).subscribe({
      next: (p) => { this.profile = p; this.error = null; },
      error: (e) => (this.error = e.error?.message ?? 'Error creating profile'),
    });
  }

  saveProfile(): void {
    this.api.updateProfile(this.orgId, this.editForm.value as Partial<BillingProfile>).subscribe({
      next: (p) => { this.profile = p; this.editMode = false; },
      error: (e) => (this.error = e.error?.message ?? 'Error updating profile'),
    });
  }
}
