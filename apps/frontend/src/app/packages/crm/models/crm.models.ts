/** CRM HTTP models aligned with Spec 017 backend schemas. */

export interface CrmPermissionsResponse {
  permissions: string[];
  roles: string[];
}

// ── Prospects ────────────────────────────────────────────────────────────────

export interface Prospect {
  id: number;
  display_name: string;
  company_name?: string | null;
  email?: string | null;
  phone?: string | null;
  source?: string | null;
  status: string;
  owner_user_id?: number | null;
  organization_id?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProspectCreateRequest {
  display_name: string;
  company_name?: string;
  email?: string;
  phone?: string;
  source?: string;
  notes?: string;
}

export interface ProspectUpdateRequest {
  display_name?: string;
  company_name?: string;
  email?: string;
  phone?: string;
  source?: string;
  notes?: string;
}

export interface ProspectContact {
  prospect_id: number;
  contact_id: number;
  is_primary: boolean;
  is_decision_maker: boolean;
  is_signatory: boolean;
  added_at: string;
}

// ── Contacts ─────────────────────────────────────────────────────────────────

export interface Contact {
  id: number;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  company_name?: string | null;
  linked_user_id?: number | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ContactCreateRequest {
  full_name: string;
  email?: string;
  phone?: string;
  company_name?: string;
}

// ── Opportunities ─────────────────────────────────────────────────────────────

export const OPPORTUNITY_STAGES = [
  'prospect',
  'qualified',
  'proposal',
  'negotiation',
  'won',
  'lost',
  'canceled',
] as const;

export type OpportunityStage = (typeof OPPORTUNITY_STAGES)[number];

export interface Opportunity {
  id: number;
  prospect_id: number;
  name: string;
  description?: string | null;
  stage: string;
  probability?: number | null;
  expected_value?: number | null;
  currency?: string | null;
  expected_close_date?: string | null;
  actual_close_date?: string | null;
  outcome?: string | null;
  owner_user_id?: number | null;
  organization_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface OpportunityCreateRequest {
  prospect_id: number;
  name: string;
  description?: string;
  expected_value?: number;
  currency?: string;
  probability?: number;
  expected_close_date?: string;
}

export interface OpportunityUpdateRequest {
  name?: string;
  description?: string;
  expected_value?: number;
  currency?: string;
  probability?: number;
  expected_close_date?: string;
}

export interface OpportunityStageHistory {
  id: number;
  opportunity_id: number;
  from_stage?: string | null;
  to_stage: string;
  actor_user_id?: number | null;
  reason?: string | null;
  occurred_at: string;
}

// ── Activities ────────────────────────────────────────────────────────────────

export interface SalesActivity {
  id: number;
  activity_type: string;
  subject: string;
  body?: string | null;
  outcome?: string | null;
  prospect_id?: number | null;
  contact_id?: number | null;
  opportunity_id?: number | null;
  actor_user_id?: number | null;
  scheduled_at?: string | null;
  completed_at?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ActivityCreateRequest {
  activity_type: string;
  subject: string;
  body?: string;
  prospect_id?: number;
  contact_id?: number;
  opportunity_id?: number;
  scheduled_at?: string;
}

// ── Quotations ────────────────────────────────────────────────────────────────

export interface Quotation {
  id: number;
  opportunity_id: number;
  status: string;
  currency?: string | null;
  notes?: string | null;
  row_version?: number | null;
  current_version_no?: number | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface QuotationCreateRequest {
  opportunity_id: number;
  currency?: string;
  notes?: string;
}

export interface QuotationVersion {
  id: number;
  quotation_id: number;
  version_no: number;
  status: string;
  subtotal?: number | null;
  discount_pct?: number | null;
  discount_requires_approval?: boolean | null;
  total?: number | null;
  notes?: string | null;
  sent_at?: string | null;
  accepted_at?: string | null;
  rejected_at?: string | null;
  is_immutable?: boolean | null;
  created_by?: number | null;
  created_at: string;
}

export interface QuotationItem {
  id: number;
  quotation_version_id: number;
  description: string;
  quantity: number;
  unit_price: number;
  discount_pct?: number | null;
  line_total?: number | null;
  plan_code?: string | null;
  sort_order?: number | null;
  created_at: string;
}

export interface QuotationItemCreateRequest {
  description: string;
  quantity: number;
  unit_price: number;
  discount_pct?: number;
  plan_code?: string;
  sort_order?: number;
}

// ── Approvals ─────────────────────────────────────────────────────────────────

export interface ApprovalRequest {
  id: number;
  object_type: string;
  object_id: number;
  reason?: string | null;
  threshold_ref?: number | null;
  status: string;
  requested_by?: number | null;
  reviewed_by?: number | null;
  review_note?: string | null;
  requested_at?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

// ── Conversions ───────────────────────────────────────────────────────────────

export interface CustomerConversion {
  id: number;
  opportunity_id: number;
  mode: string;
  status: string;
  organization_id?: number | null;
  contact_id?: number | null;
  signatory_user_id?: number | null;
  claim_token_expires_at?: string | null;
  claim_consumed_at?: string | null;
  idempotency_key?: string | null;
  requested_by?: number | null;
  completed_at?: string | null;
  failure_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversionPrepareRequest {
  opportunity_id: number;
  mode: 'link' | 'claim';
  contact_id?: number;
  idempotency_key?: string;
}

export interface ConversionPrepareResponse {
  conversion: CustomerConversion;
  claim_token?: string | null;
  claim_token_note?: string | null;
}

// ── Contracts ─────────────────────────────────────────────────────────────────

export interface CommercialContract {
  id: number;
  quotation_version_id: number;
  opportunity_id: number;
  organization_id?: number | null;
  legal_name?: string | null;
  signatory_user_id?: number | null;
  signatory_contact_id?: number | null;
  status: string;
  acceptance_evidence?: string | null;
  accepted_at?: string | null;
  rejected_at?: string | null;
  expired_at?: string | null;
  terminated_at?: string | null;
  termination_reason?: string | null;
  approved_by?: number | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

// ── Audit ─────────────────────────────────────────────────────────────────────

export interface CrmAuditEntry {
  id: number;
  organization_id?: number | null;
  actor_user_id?: number | null;
  action: string;
  target_type: string;
  target_id?: string | null;
  source: string;
  result: string;
  reason?: string | null;
  occurred_at: string;
  previous_values?: Record<string, unknown> | null;
  new_values?: Record<string, unknown> | null;
}

// ── Shared ────────────────────────────────────────────────────────────────────

export interface Paginated<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
}

export interface CrmApiErrorBody {
  status?: string;
  message?: string;
  details?: { code?: string; status_code?: number; [k: string]: unknown };
}
