export interface TermsVersion {
  id: number;
  version_code: string;
  title: string;
  content_summary: string;
  status: string;
}

export interface ConsentDefinition {
  id: number;
  code: string;
  title: string;
  description: string;
  is_required: boolean;
  status: string;
}

export interface ConsentRecord {
  id: number;
  consent_definition_id: number;
  status: string;
}

export interface DataRequest {
  id: number;
  request_type: string;
  status: string;
  reason?: string;
}

export interface PaginatedTerms {
  items: TermsVersion[];
  total: number;
}

export interface PaginatedDataRequests {
  items: DataRequest[];
  total: number;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  source: string;
  target_type: string;
  occurred_at: string;
}

export interface PaginatedAudit {
  items: AuditLogEntry[];
  total: number;
}
