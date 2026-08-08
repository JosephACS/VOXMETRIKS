> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 026 — Compliance, Privacy and Global Audit

**Status:** IMPLEMENTATION_COMPLETE  
**API:** `/api/v1/compliance`

## Scope
Terms versions/acceptance; consent definitions/records/withdrawal; DSR (access/export/correction/deletion); retention policies/executions; legal hold; security incidents; sensitive access with reason; org and platform audit search.

## Tables (12)
`app_terms_version`, `app_terms_acceptance`, `app_consent_definition`, `app_consent_record`, `app_data_request`, `app_data_request_action`, `app_retention_policy`, `app_retention_execution`, `app_legal_hold`, `app_security_incident`, `app_incident_action`, `app_sensitive_access_record`.

## Permissions
Org: `compliance.view`, `compliance.manage`, `privacy.request`, `privacy.export`, `incident.manage`, `audit.search`  
Platform: `audit.search` (global)

## Constraints
No silent delete; legal hold/retention block deletion; sanitized export; append-only audit via `compliance.use_case`; minimize PII; sensitive access requires reason. No GDPR/PCI/ISO certification claims.
