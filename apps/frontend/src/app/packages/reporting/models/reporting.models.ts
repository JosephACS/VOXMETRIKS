export interface ReportDefinition {
  id: number;
  organization_id: number;
  code: string;
  title: string;
  description: string;
  status: string;
  default_period: string;
}

export interface ExecutiveReport {
  id: number;
  organization_id: number;
  definition_id: number;
  generation_id: number;
  snapshot_id: number;
  title: string;
  status: string;
  period_start?: string | null;
  period_end?: string | null;
}

export interface BusinessDecision {
  id: number;
  organization_id: number;
  executive_report_id?: number | null;
  title: string;
  proposal: string;
  status: string;
}

export interface DecisionAction {
  id: number;
  decision_id: number;
  title: string;
  status: string;
}

export interface DecisionFollowUp {
  id: number;
  decision_id: number;
  note: string;
  created_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
