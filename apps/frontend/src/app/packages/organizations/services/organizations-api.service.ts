import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import {
  ApiErrorBody,
  AuditEntry,
  BusinessRole,
  CurrentOrganizationResponse,
  Invitation,
  InvitationCreateResponse,
  Membership,
  Organization,
  OrganizationCreateRequest,
  OrganizationCreateResponse,
  Paginated,
  Permission,
} from '../models/organization.models';

export class OrganizationsApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly body?: ApiErrorBody,
  ) {
    super(message);
    this.name = 'OrganizationsApiError';
  }
}

@Injectable({ providedIn: 'root' })
export class OrganizationsApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}`;

  private handle = (err: unknown) => {
    if (err instanceof HttpErrorResponse) {
      const body = err.error as ApiErrorBody | undefined;
      const code = body?.details?.code;
      const message = body?.message || err.message || 'Request failed';
      return throwError(() => new OrganizationsApiError(message, err.status, code, body));
    }
    return throwError(() => err);
  };

  listMine(): Observable<Organization[]> {
    return this.http
      .get<Organization[]>(`${this.base}/organizations`)
      .pipe(catchError(this.handle));
  }

  create(body: OrganizationCreateRequest): Observable<OrganizationCreateResponse> {
    return this.http
      .post<OrganizationCreateResponse>(`${this.base}/organizations`, body)
      .pipe(catchError(this.handle));
  }

  get(id: number): Observable<Organization> {
    return this.http
      .get<Organization>(`${this.base}/organizations/${id}`)
      .pipe(catchError(this.handle));
  }

  update(id: number, body: Partial<OrganizationCreateRequest>): Observable<Organization> {
    return this.http
      .patch<Organization>(`${this.base}/organizations/${id}`, body)
      .pipe(catchError(this.handle));
  }

  close(id: number, reason?: string): Observable<Organization> {
    return this.http
      .post<Organization>(`${this.base}/organizations/${id}/close`, { reason })
      .pipe(catchError(this.handle));
  }

  getCurrent(): Observable<CurrentOrganizationResponse> {
    return this.http
      .get<CurrentOrganizationResponse>(`${this.base}/organizations/current`)
      .pipe(catchError(this.handle));
  }

  activate(id: number): Observable<CurrentOrganizationResponse> {
    return this.http
      .post<CurrentOrganizationResponse>(`${this.base}/organizations/${id}/activate`, {})
      .pipe(catchError(this.handle));
  }

  listMembers(orgId: number, page = 1, limit = 50): Observable<Paginated<Membership>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http
      .get<Paginated<Membership>>(`${this.base}/organizations/${orgId}/members`, { params })
      .pipe(catchError(this.handle));
  }

  memberAction(
    orgId: number,
    memberId: number,
    action: 'suspend' | 'reactivate' | 'leave',
  ): Observable<Membership> {
    return this.http
      .patch<Membership>(`${this.base}/organizations/${orgId}/members/${memberId}`, { action })
      .pipe(catchError(this.handle));
  }

  removeMember(orgId: number, memberId: number): Observable<Membership> {
    return this.http
      .post<Membership>(`${this.base}/organizations/${orgId}/members/${memberId}/remove`, {})
      .pipe(catchError(this.handle));
  }

  listInvitations(orgId: number, page = 1, limit = 50): Observable<Paginated<Invitation>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http
      .get<Paginated<Invitation>>(`${this.base}/organizations/${orgId}/invitations`, { params })
      .pipe(catchError(this.handle));
  }

  createInvitation(
    orgId: number,
    email: string,
    roleCodes: string[],
    ttlDays = 7,
  ): Observable<InvitationCreateResponse> {
    return this.http
      .post<InvitationCreateResponse>(`${this.base}/organizations/${orgId}/invitations`, {
        email,
        role_codes: roleCodes,
        ttl_days: ttlDays,
      })
      .pipe(catchError(this.handle));
  }

  revokeInvitation(orgId: number, invitationId: number): Observable<Invitation> {
    return this.http
      .post<Invitation>(
        `${this.base}/organizations/${orgId}/invitations/${invitationId}/revoke`,
        {},
      )
      .pipe(catchError(this.handle));
  }

  resendInvitation(orgId: number, invitationId: number): Observable<InvitationCreateResponse> {
    return this.http
      .post<InvitationCreateResponse>(
        `${this.base}/organizations/${orgId}/invitations/${invitationId}/resend`,
        {},
      )
      .pipe(catchError(this.handle));
  }

  acceptInvitation(token: string): Observable<{ organization: Organization; membership: Membership }> {
    return this.http
      .post<{ organization: Organization; membership: Membership }>(
        `${this.base}/invitations/${encodeURIComponent(token)}/accept`,
        {},
      )
      .pipe(catchError(this.handle));
  }

  listRoles(orgId: number): Observable<BusinessRole[]> {
    return this.http
      .get<BusinessRole[]>(`${this.base}/organizations/${orgId}/roles`)
      .pipe(catchError(this.handle));
  }

  listPermissions(orgId: number): Observable<Permission[]> {
    return this.http
      .get<Permission[]>(`${this.base}/organizations/${orgId}/permissions`)
      .pipe(catchError(this.handle));
  }

  putMemberRoles(
    orgId: number,
    memberId: number,
    assign: string[],
    revoke: string[],
  ): Observable<string[]> {
    return this.http
      .put<string[]>(`${this.base}/organizations/${orgId}/members/${memberId}/roles`, {
        assign,
        revoke,
      })
      .pipe(catchError(this.handle));
  }

  listAudit(orgId: number, page = 1, limit = 50): Observable<Paginated<AuditEntry>> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http
      .get<Paginated<AuditEntry>>(`${this.base}/organizations/${orgId}/audit-log`, { params })
      .pipe(catchError(this.handle));
  }
}
