export interface Campaign {
  id: number;
  organization_id: number;
  name: string;
  status: string;
  market?: string | null;
  segment?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  artist_profile_id?: number | null;
  catalog_release_id?: number | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignBudget {
  id: number;
  campaign_id: number;
  organization_id: number;
  amount: number;
  currency: string;
  approval_threshold?: number | null;
  override_approved: boolean;
}

export interface CampaignExpense {
  id: number;
  campaign_id: number;
  amount: number;
  currency: string;
  category: string;
  description?: string | null;
  expense_date: string;
  recorded_by: number;
}

export interface CampaignApproval {
  id: number;
  campaign_id: number;
  approval_type: string;
  status: string;
  requested_by: number;
  decided_by?: number | null;
  decision_reason?: string | null;
  requested_at: string;
  decided_at?: string | null;
}

export interface CampaignRoiSnapshot {
  id: number;
  campaign_id: number;
  status: string;
  roi_value?: number | null;
  unavailable_reason?: string | null;
  cost_per_result?: number | null;
  budget_utilization?: number | null;
  goal_attainment?: number | null;
  engagement_lift?: number | null;
  currency?: string | null;
  computed_at: string;
}

export interface PaginatedCampaigns {
  items: Campaign[];
  total: number;
  page: number;
  page_size: number;
}
