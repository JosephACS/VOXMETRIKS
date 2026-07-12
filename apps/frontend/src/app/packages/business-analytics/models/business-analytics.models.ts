export interface KpiDefinition {
  id: number;
  code: string;
  name: string;
  formula_description: string;
  version: number;
  source_type: string;
  null_handling: string;
}

export interface KpiSnapshot {
  id: number;
  period: string;
  value?: number | null;
  quality_status: string;
  source_label: string;
  is_synthetic: boolean;
}

export interface BusinessAlert {
  id: number;
  severity: string;
  title: string;
  body: string;
  status: string;
  kpi_code?: string | null;
}

export interface Recommendation {
  id: number;
  rule_code: string;
  title: string;
  rationale: string;
  evidence_ref?: string | null;
  is_ai: boolean;
}

export interface DashboardOverview {
  organization_id: number;
  period: string;
  kpis: Record<string, { value?: number | null; source_label: string; quality_status: string; is_synthetic: boolean }>;
  recurring_revenue?: {
    active_mrr?: number | null;
    active_arr?: number | null;
    primary_currency?: string | null;
    past_due_by_currency?: Array<{ currency: string; mrr: number; arr: number }>;
    total_recurring_exposure_by_currency?: Array<{ currency: string; mrr: number; arr: number }>;
    quality_status?: string;
    policy?: Record<string, string>;
  } | null;
}
