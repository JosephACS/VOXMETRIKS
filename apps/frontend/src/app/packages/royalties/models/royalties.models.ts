/** Spec 030 — royalty pools, settlements, statements, simulated payouts. */

export interface RoyaltyPool {
  id: number;
  organization_id: number | null;
  currency: string;
  period_start: string;
  period_end: string;
  status: string;
  attribution_method: string;
  total_amount: string | number;
  residual_amount: string | number;
  label: string | null;
  is_demo: boolean;
  idempotency_key: string;
  created_by: number;
  approved_by: number | null;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  sources?: Record<string, string | number | null | undefined>[] | null;
}

export interface RoyaltySettlement {
  id: number;
  pool_id: number;
  status: string;
  currency: string;
  gross_total: string | number;
  adjustment_total: string | number;
  net_total: string | number;
  block_conflict_id: number | null;
  idempotency_key: string;
  created_by: number;
  approved_by: number | null;
  finalized_at: string | null;
  created_at: string;
  updated_at: string;
  block_reason: string | null;
  asset_allocations?: Record<string, string | number | null | undefined>[] | null;
  party_allocations?: Record<string, string | number | null | undefined>[] | null;
}

export interface RoyaltyStatement {
  id: number;
  settlement_run_id: number;
  party_id: number;
  party_name: string;
  period_start: string;
  period_end: string;
  currency: string;
  gross_amount: string | number;
  adjustment_amount: string | number;
  net_amount: string | number;
  status: string;
  export_json: string | null;
  created_at: string;
}

export interface PayoutBatch {
  id: number;
  settlement_run_id: number;
  status: string;
  currency: string;
  total_amount: string | number;
  idempotency_key: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  instructions?: Record<string, string | number | null | undefined>[] | null;
  simulated_only: boolean;
}

export interface RoyaltyMetrics {
  income_note: string;
  distributable_pool_approved: string | number;
  distributable_pool_allocated_or_closed: string | number;
  pool_count: number;
  settlement_gross_total: string | number;
  settlement_net_total: string | number;
  settlement_count: number;
  payout_paid_simulated_total: string | number;
  payout_batch_count: number;
  simulated_only: boolean;
}
