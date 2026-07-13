/** HTTP models aligned with Spec 016 I3 contracts. */

export interface Organization {
  id: number;
  display_name: string;
  legal_name?: string | null;
  slug: string;
  organization_type: string;
  country_code?: string | null;
  timezone: string;
  default_currency: string;
  status: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  is_demo?: boolean;
  is_test?: boolean;
}

export interface Membership {
  id: number;
  organization_id: number;
  user_id: number;
  status: string;
  joined_at?: string | null;
  suspended_at?: string | null;
  left_at?: string | null;
  removed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrganizationCreateRequest {
  display_name: string;
  slug?: string;
  organization_type?: string;
  legal_name?: string;
  country_code?: string;
  timezone?: string;
  default_currency?: string;
  activate?: boolean;
}

export interface OrganizationCreateResponse {
  organization: Organization;
  membership: Membership;
  roles: string[];
  reused_existing?: boolean;
  idempotency_mode?: string;
}

export interface CurrentOrganizationResponse {
  context: 'none' | 'active' | 'invalid' | 'access_revoked';
  organization?: Organization | null;
  membership?: Membership | null;
  roles?: string[];
  permissions?: string[];
  source?: string | null;
}

export interface Invitation {
  id: number;
  organization_id: number;
  email_normalized: string;
  status: string;
  expires_at: string;
  invited_by: number;
  initial_role_code: string;
  accepted_by?: number | null;
  accepted_at?: string | null;
  revoked_by?: number | null;
  revoked_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvitationCreateResponse {
  invitation_id: number;
  expires_at: string;
  invite_token?: string | null;
  returned_once?: boolean;
  delivery_status: string;
  invitation: Invitation;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
}

export interface BusinessRole {
  id: number;
  code: string;
  display_name: string;
  description: string;
  scope: string;
  is_system: boolean;
  is_active: boolean;
}

export interface Permission {
  id: number;
  code: string;
  description: string;
  domain: string;
  is_active: boolean;
}

export interface AuditEntry {
  id: number;
  organization_id?: number | null;
  actor_user_id?: number | null;
  action: string;
  target_type: string;
  target_id?: string | null;
  reason?: string | null;
  request_id?: string | null;
  source: string;
  result: string;
  occurred_at: string;
  previous_values?: Record<string, unknown> | null;
  new_values?: Record<string, unknown> | null;
}

export interface ApiErrorBody {
  status?: string;
  message?: string;
  details?: { code?: string; status_code?: number; [k: string]: unknown };
}
