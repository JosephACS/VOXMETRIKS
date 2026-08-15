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
  status_label?: string | null;
  joined_at?: string | null;
  suspended_at?: string | null;
  left_at?: string | null;
  removed_at?: string | null;
  created_at: string;
  updated_at: string;
  user?: { display_name: string; email?: string | null } | null;
  roles?: { code: string; label: string }[];
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
  client_intent_id?: string;
}

export interface OrganizationJourney {
  organization: {
    id: number;
    display_name: string;
    organization_type?: string;
    legal_name?: string | null;
    country_code?: string | null;
    timezone?: string;
    default_currency?: string;
    status?: string;
  };
  membership?: { id: number; status: string; status_label?: string } | null;
  access_tier: string;
  completed_steps: string[];
  next_action: string;
  capabilities: {
    update_profile: boolean;
    choose_plan: boolean;
    resume_checkout: boolean;
    invite_team: boolean;
    view_members: boolean;
    enter_workspace: boolean;
    complete_journey: boolean;
  };
  subscription: {
    status?: string | null;
    plan_name?: string | null;
    trial?: boolean;
  };
  checkout?: {
    id: number;
    status: string;
    plan_code: string;
    amount?: number | null;
    currency?: string | null;
    failure_code?: string | null;
    checkout_url: string;
  } | null;
  team: { active_members: number; pending_invitations: number };
  allowed_destinations: string[];
  onboarding_status?: string;
  journey_url?: string | null;
}

export interface OrganizationCreateResponse {
  organization: Organization;
  membership: Membership;
  roles: string[];
  reused_existing?: boolean;
  idempotency_mode?: string;
  next_action?: string | null;
  journey_url?: string | null;
  journey?: OrganizationJourney | null;
}

export interface InvitationRoleOption {
  code: string;
  label: string;
  description?: string;
}

export interface OrganizationCatalogs {
  organization_types: { code: string; label: string }[];
  countries: { code: string; label: string }[];
  timezones: { code: string; label: string }[];
  currencies: { code: string; label: string }[];
}

export interface OrgSubscriptionAccess {
  has_subscription: boolean;
  status?: string | null;
  access_state?: string | null;
  tier?: string;
}

export interface CurrentOrganizationResponse {
  context: 'none' | 'active' | 'invalid' | 'access_revoked';
  organization?: Organization | null;
  membership?: Membership | null;
  roles?: string[];
  permissions?: string[];
  source?: string | null;
  subscription_access?: OrgSubscriptionAccess | null;
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
