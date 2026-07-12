# Data model — Spec 026

**Status:** IMPLEMENTATION_COMPLETE  
**Honesty:** No GDPR/PCI/ISO/SRI certification claimed.

## Tables
| Table | Purpose |
|-------|---------|
| app_terms_version | Versioned terms of service / privacy notice |
| app_terms_acceptance | User/org acceptance of a terms version |
| app_consent_definition | Configurable consent purpose |
| app_consent_record | Grant / withdrawal of consent |
| app_data_request | DSR: access, export, correction, deletion |
| app_data_request_action | Actions taken on a DSR |
| app_retention_policy | Retention rules by subject type |
| app_retention_execution | Record of retention runs (conceptual) |
| app_legal_hold | Blocks deletion while active |
| app_security_incident | Security incident register |
| app_incident_action | Response actions on incidents |
| app_sensitive_access_record | Access to sensitive data with reason |

## Scope
Organization-scoped for most records; platform audit search via platform RBAC `audit.search`.
