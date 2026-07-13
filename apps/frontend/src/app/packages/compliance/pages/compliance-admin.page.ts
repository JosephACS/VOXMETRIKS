import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ComplianceApiService } from '../services/compliance-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { DataRequest, TermsVersion } from '../models/compliance.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-compliance-admin',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="compliance-admin">
      <h1>{{ 'compliance.admin.title' | t:lang() }}</h1>
      <p class="subtitle">Terms, DSR, retention, incidents, and audit search.</p>
      <nav class="subnav">
        <a routerLink="/compliance">{{ 'compliance.privacy.title' | t:lang() }}</a>
      </nav>

      <section>
        <h2>Terms Versions</h2>
        @if (terms.length === 0) { <p>No terms versions.</p> }
        @else {
          <table>
            <thead><tr><th>Code</th><th>Title</th><th>Status</th></tr></thead>
            <tbody>
              @for (t of terms; track t.id) {
                <tr><td>{{ t.version_code }}</td><td>{{ t.title }}</td><td>{{ t.status }}</td></tr>
              }
            </tbody>
          </table>
        }
      </section>

      <section>
        <h2>Data Subject Requests</h2>
        @if (dsr.length === 0) { <p>No DSR requests.</p> }
        @else {
          <table>
            <thead><tr><th>ID</th><th>Type</th><th>Status</th></tr></thead>
            <tbody>
              @for (d of dsr; track d.id) {
                <tr><td>{{ d.id }}</td><td>{{ d.request_type }}</td><td>{{ d.status }}</td></tr>
              }
            </tbody>
          </table>
        }
      </section>

      @if (error) { <p class="error">{{ error }}</p> }
    </div>
  `,
})
export class ComplianceAdminPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ComplianceApiService);
  private orgCtx = inject(OrganizationContextService);

  terms: TermsVersion[] = [];
  dsr: DataRequest[] = [];
  error: string | null = null;

  ngOnInit(): void { this.load(); }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) { this.error = this.i18n.t('common.orgRequired'); return; }
    this.api.listTerms(orgId).subscribe({
      next: (r) => { this.terms = r.items; },
      error: (e) => { this.error = e?.error?.message || 'Failed to load terms'; },
    });
    this.api.listDsr(orgId).subscribe({
      next: (r) => { this.dsr = r.items; },
      error: (e) => { this.error = e?.error?.message || 'Failed to load DSR'; },
    });
  }
}
