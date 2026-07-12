# Data model — Spec 027

**Status:** IMPLEMENTATION_COMPLETE  
**Honesty:** Academic/local ops only — not production HA, email, or DR.

## Tables
| Table | Purpose |
|-------|---------|
| app_notification | In-app / console notification |
| app_notification_delivery | Delivery attempt log |
| app_provider_configuration | Provider config with secret_ref (no raw secrets) |
| app_webhook_event | Inbound webhook event (idempotent key) |
| app_webhook_delivery | Outbound/inbound delivery attempts |
| app_background_job | Job definition |
| app_job_execution | Execution + retry / DLQ status |
| app_feature_flag | Feature flags |
| app_operational_incident | Ops incidents |
| app_backup_record | Academic backup job record |
| app_restore_verification | Local restore verification result |

## Ports
NotificationPort, EmailPort (ConsoleMock labeled MOCK), PaymentProvider registry (billing reuse).
