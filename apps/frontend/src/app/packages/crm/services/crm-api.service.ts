import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import {
  ActivityCreateRequest,
  ApprovalRequest,
  CommercialContract,
  Contact,
  ContactCreateRequest,
  ConversionPrepareRequest,
  ConversionPrepareResponse,
  CrmApiErrorBody,
  CrmAuditEntry,
  CrmPermissionsResponse,
  CustomerConversion,
  Opportunity,
  OpportunityCreateRequest,
  OpportunityStageHistory,
  OpportunityUpdateRequest,
  Paginated,
  Prospect,
  ProspectContact,
  ProspectCreateRequest,
  ProspectUpdateRequest,
  Quotation,
  QuotationCreateRequest,
  QuotationItem,
  QuotationItemCreateRequest,
  QuotationVersion,
  SalesActivity,
} from '../models/crm.models';

export class CrmApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly body?: CrmApiErrorBody,
  ) {
    super(message);
    this.name = 'CrmApiError';
  }
}

@Injectable({ providedIn: 'root' })
export class CrmApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/crm`;

  private handle = (err: unknown) => {
    if (err instanceof HttpErrorResponse) {
      const body = err.error as CrmApiErrorBody | undefined;
      const code = body?.details?.code;
      const message = body?.message || err.message || 'CRM request failed';
      return throwError(() => new CrmApiError(message, err.status, code, body));
    }
    return throwError(() => err);
  };

  // ── Permissions ───────────────────────────────────────────────────────────

  getPermissions(): Observable<CrmPermissionsResponse> {
    return this.http
      .get<CrmPermissionsResponse>(`${this.base}/permissions`)
      .pipe(catchError(this.handle));
  }

  // ── Prospects ─────────────────────────────────────────────────────────────

  listProspects(page = 1, limit = 25, status?: string): Observable<Paginated<Prospect>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (status) params = params.set('status', status);
    return this.http
      .get<Paginated<Prospect>>(`${this.base}/prospects`, { params })
      .pipe(catchError(this.handle));
  }

  getProspect(id: number): Observable<Prospect> {
    return this.http
      .get<Prospect>(`${this.base}/prospects/${id}`)
      .pipe(catchError(this.handle));
  }

  createProspect(body: ProspectCreateRequest): Observable<Prospect> {
    return this.http
      .post<Prospect>(`${this.base}/prospects`, body)
      .pipe(catchError(this.handle));
  }

  updateProspect(id: number, body: ProspectUpdateRequest): Observable<Prospect> {
    return this.http
      .patch<Prospect>(`${this.base}/prospects/${id}`, body)
      .pipe(catchError(this.handle));
  }

  transitionProspectStatus(id: number, status: string): Observable<Prospect> {
    return this.http
      .post<Prospect>(`${this.base}/prospects/${id}/status`, { status })
      .pipe(catchError(this.handle));
  }

  linkContactToProspect(
    prospectId: number,
    contactId: number,
    isPrimary = false,
    isDecisionMaker = false,
    isSignatory = false,
  ): Observable<ProspectContact> {
    return this.http
      .post<ProspectContact>(`${this.base}/prospects/${prospectId}/contacts`, {
        contact_id: contactId,
        is_primary: isPrimary,
        is_decision_maker: isDecisionMaker,
        is_signatory: isSignatory,
      })
      .pipe(catchError(this.handle));
  }

  // ── Contacts ──────────────────────────────────────────────────────────────

  listContacts(page = 1, limit = 25): Observable<Paginated<Contact>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http
      .get<Paginated<Contact>>(`${this.base}/contacts`, { params })
      .pipe(catchError(this.handle));
  }

  getContact(id: number): Observable<Contact> {
    return this.http
      .get<Contact>(`${this.base}/contacts/${id}`)
      .pipe(catchError(this.handle));
  }

  createContact(body: ContactCreateRequest): Observable<Contact> {
    return this.http
      .post<Contact>(`${this.base}/contacts`, body)
      .pipe(catchError(this.handle));
  }

  // ── Opportunities ─────────────────────────────────────────────────────────

  listOpportunities(
    page = 1,
    limit = 50,
    stage?: string,
    prospectId?: number,
  ): Observable<Paginated<Opportunity>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (stage) params = params.set('stage', stage);
    if (prospectId != null) params = params.set('prospect_id', prospectId);
    return this.http
      .get<Paginated<Opportunity>>(`${this.base}/opportunities`, { params })
      .pipe(catchError(this.handle));
  }

  getOpportunity(id: number): Observable<Opportunity> {
    return this.http
      .get<Opportunity>(`${this.base}/opportunities/${id}`)
      .pipe(catchError(this.handle));
  }

  createOpportunity(body: OpportunityCreateRequest): Observable<Opportunity> {
    return this.http
      .post<Opportunity>(`${this.base}/opportunities`, body)
      .pipe(catchError(this.handle));
  }

  updateOpportunity(id: number, body: OpportunityUpdateRequest): Observable<Opportunity> {
    return this.http
      .patch<Opportunity>(`${this.base}/opportunities/${id}`, body)
      .pipe(catchError(this.handle));
  }

  advanceOpportunityStage(id: number, stage: string, reason?: string): Observable<Opportunity> {
    return this.http
      .post<Opportunity>(`${this.base}/opportunities/${id}/stage`, { stage, reason })
      .pipe(catchError(this.handle));
  }

  closeOpportunity(
    id: number,
    outcome: string,
    stage: string,
    reason?: string,
  ): Observable<Opportunity> {
    return this.http
      .post<Opportunity>(`${this.base}/opportunities/${id}/close`, { outcome, stage, reason })
      .pipe(catchError(this.handle));
  }

  getOpportunityStageHistory(id: number): Observable<OpportunityStageHistory[]> {
    return this.http
      .get<OpportunityStageHistory[]>(`${this.base}/opportunities/${id}/stage-history`)
      .pipe(catchError(this.handle));
  }

  // ── Activities ────────────────────────────────────────────────────────────

  listActivities(
    page = 1,
    limit = 25,
    opportunityId?: number,
    prospectId?: number,
  ): Observable<Paginated<SalesActivity>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (opportunityId != null) params = params.set('opportunity_id', opportunityId);
    if (prospectId != null) params = params.set('prospect_id', prospectId);
    return this.http
      .get<Paginated<SalesActivity>>(`${this.base}/activities`, { params })
      .pipe(catchError(this.handle));
  }

  createActivity(body: ActivityCreateRequest): Observable<SalesActivity> {
    return this.http
      .post<SalesActivity>(`${this.base}/activities`, body)
      .pipe(catchError(this.handle));
  }

  // ── Quotations ────────────────────────────────────────────────────────────

  listQuotations(page = 1, limit = 25, opportunityId?: number): Observable<Paginated<Quotation>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (opportunityId != null) params = params.set('opportunity_id', opportunityId);
    return this.http
      .get<Paginated<Quotation>>(`${this.base}/quotations`, { params })
      .pipe(catchError(this.handle));
  }

  getQuotation(id: number): Observable<Quotation> {
    return this.http
      .get<Quotation>(`${this.base}/quotations/${id}`)
      .pipe(catchError(this.handle));
  }

  createQuotation(body: QuotationCreateRequest): Observable<Quotation> {
    return this.http
      .post<Quotation>(`${this.base}/quotations`, body)
      .pipe(catchError(this.handle));
  }

  listQuotationVersions(quotationId: number): Observable<QuotationVersion[]> {
    return this.http
      .get<QuotationVersion[]>(`${this.base}/quotations/${quotationId}/versions`)
      .pipe(catchError(this.handle));
  }

  createQuotationVersion(quotationId: number, notes?: string): Observable<QuotationVersion> {
    return this.http
      .post<QuotationVersion>(`${this.base}/quotations/${quotationId}/versions`, { notes })
      .pipe(catchError(this.handle));
  }

  getQuotationVersion(versionId: number): Observable<QuotationVersion> {
    return this.http
      .get<QuotationVersion>(`${this.base}/quotation-versions/${versionId}`)
      .pipe(catchError(this.handle));
  }

  listQuotationItems(versionId: number): Observable<QuotationItem[]> {
    return this.http
      .get<QuotationItem[]>(`${this.base}/quotation-versions/${versionId}/items`)
      .pipe(catchError(this.handle));
  }

  addQuotationItem(versionId: number, body: QuotationItemCreateRequest): Observable<QuotationItem> {
    return this.http
      .post<QuotationItem>(`${this.base}/quotation-versions/${versionId}/items`, body)
      .pipe(catchError(this.handle));
  }

  sendQuotationVersion(versionId: number): Observable<QuotationVersion> {
    return this.http
      .post<QuotationVersion>(`${this.base}/quotation-versions/${versionId}/send`, {})
      .pipe(catchError(this.handle));
  }

  requestDiscountApproval(versionId: number, reason: string): Observable<ApprovalRequest> {
    return this.http
      .post<ApprovalRequest>(`${this.base}/quotation-versions/${versionId}/request-approval`, {
        reason,
      })
      .pipe(catchError(this.handle));
  }

  // ── Approvals ─────────────────────────────────────────────────────────────

  listApprovals(page = 1, limit = 25): Observable<Paginated<ApprovalRequest>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http
      .get<Paginated<ApprovalRequest>>(`${this.base}/approvals`, { params })
      .pipe(catchError(this.handle));
  }

  getApproval(id: number): Observable<ApprovalRequest> {
    return this.http
      .get<ApprovalRequest>(`${this.base}/approvals/${id}`)
      .pipe(catchError(this.handle));
  }

  approveRequest(id: number, reviewNote?: string): Observable<ApprovalRequest> {
    return this.http
      .post<ApprovalRequest>(`${this.base}/approvals/${id}/approve`, { review_note: reviewNote })
      .pipe(catchError(this.handle));
  }

  rejectRequest(id: number, reviewNote?: string): Observable<ApprovalRequest> {
    return this.http
      .post<ApprovalRequest>(`${this.base}/approvals/${id}/reject`, { review_note: reviewNote })
      .pipe(catchError(this.handle));
  }

  // ── Conversions ───────────────────────────────────────────────────────────

  listConversions(
    page = 1,
    limit = 25,
    opportunityId?: number,
    status?: string,
  ): Observable<Paginated<CustomerConversion>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (opportunityId != null) params = params.set('opportunity_id', opportunityId);
    if (status) params = params.set('status', status);
    return this.http
      .get<Paginated<CustomerConversion>>(`${this.base}/conversions`, { params })
      .pipe(catchError(this.handle));
  }

  prepareConversion(body: ConversionPrepareRequest): Observable<ConversionPrepareResponse> {
    return this.http
      .post<ConversionPrepareResponse>(`${this.base}/conversions`, body)
      .pipe(catchError(this.handle));
  }

  getConversion(id: number): Observable<CustomerConversion> {
    return this.http
      .get<CustomerConversion>(`${this.base}/conversions/${id}`)
      .pipe(catchError(this.handle));
  }

  confirmLinkConversion(
    id: number,
    organizationId: number,
  ): Observable<CustomerConversion> {
    return this.http
      .post<CustomerConversion>(`${this.base}/conversions/${id}/confirm-link`, {
        organization_id: organizationId,
      })
      .pipe(catchError(this.handle));
  }

  claimConversion(
    id: number,
    token: string,
    orgDisplayName: string,
    orgSlug: string,
    orgType = 'business',
    timezone = 'UTC',
    defaultCurrency = 'USD',
    countryCode?: string,
  ): Observable<CustomerConversion> {
    return this.http
      .post<CustomerConversion>(`${this.base}/conversions/${id}/claim`, {
        token,
        org_display_name: orgDisplayName,
        org_slug: orgSlug,
        org_type: orgType,
        timezone,
        default_currency: defaultCurrency,
        country_code: countryCode,
      })
      .pipe(catchError(this.handle));
  }

  // ── Contracts ─────────────────────────────────────────────────────────────

  listContracts(
    page = 1,
    limit = 25,
    opportunityId?: number,
    status?: string,
  ): Observable<Paginated<CommercialContract>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (opportunityId != null) params = params.set('opportunity_id', opportunityId);
    if (status) params = params.set('status', status);
    return this.http
      .get<Paginated<CommercialContract>>(`${this.base}/contracts`, { params })
      .pipe(catchError(this.handle));
  }

  getContract(id: number): Observable<CommercialContract> {
    return this.http
      .get<CommercialContract>(`${this.base}/contracts/${id}`)
      .pipe(catchError(this.handle));
  }

  submitContract(id: number): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/submit`, {})
      .pipe(catchError(this.handle));
  }

  approveContract(id: number, approvalNotes?: string): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/approve`, {
        reason: approvalNotes,
      })
      .pipe(catchError(this.handle));
  }

  sendContract(id: number): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/send`, {})
      .pipe(catchError(this.handle));
  }

  acceptContract(id: number, acceptanceEvidence: string): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/accept`, {
        acceptance_evidence: acceptanceEvidence,
      })
      .pipe(catchError(this.handle));
  }

  rejectContract(id: number, reason?: string): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/reject`, { reason })
      .pipe(catchError(this.handle));
  }

  expireContract(id: number): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/expire`, {})
      .pipe(catchError(this.handle));
  }

  terminateContract(id: number, reason: string): Observable<CommercialContract> {
    return this.http
      .post<CommercialContract>(`${this.base}/contracts/${id}/terminate`, { reason })
      .pipe(catchError(this.handle));
  }

  // ── CRM Audit ─────────────────────────────────────────────────────────────

  listCrmAudit(page = 1, limit = 50): Observable<Paginated<CrmAuditEntry>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http
      .get<Paginated<CrmAuditEntry>>(`${this.base}/audit`, { params })
      .pipe(catchError(this.handle));
  }
}
