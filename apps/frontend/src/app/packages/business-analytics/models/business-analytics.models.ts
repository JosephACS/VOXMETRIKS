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

export type StrategicClassification = 'real' | 'synthetic' | 'proxy' | 'simulated' | 'unavailable';

export interface StrategicKpi {
  id?: number;
  organization_id?: number | null;
  objective_code: string;
  kpi_code: string;
  period_start: string;
  period_end: string;
  value?: number | null;
  unit: string;
  source_label: string;
  quality_status: string;
  is_synthetic: boolean;
  is_proxy: boolean;
  availability_status: string;
  unavailable_reason?: string | null;
  computed_at?: string;
  classification?: StrategicClassification | string;
}

export interface StrategicObjective {
  objective_code: string;
  title: string;
  kpi?: StrategicKpi | null;
  kpis: StrategicKpi[];
  period_start: string;
  period_end: string;
  evidence_path?: string | null;
  report_path?: string | null;
  decision_path?: string | null;
  trend?: { current: number; previous: number; delta: number } | null;
  empty: boolean;
}

export interface StrategicOverview {
  organization_id: number;
  period_start: string;
  period_end: string;
  include_global: boolean;
  comparable_periods: number;
  objectives: StrategicObjective[];
  decision_capability: {
    can_create_decision: boolean;
    can_draft_report: boolean;
    can_refresh_strategic: boolean;
    is_ai: boolean;
    recommendation_mode: string;
  };
}

export interface StrategicRefreshResult {
  organization_id?: number | null;
  period_start: string;
  period_end: string;
  include_global: boolean;
  rows_written: number;
}
