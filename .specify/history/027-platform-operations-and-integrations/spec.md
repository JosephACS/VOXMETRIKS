> **Nota histórica:** este documento es intención histórica de Spec-Driven Development.
> No es fuente del estado actual del producto.
> La verdad vigente está en [`docs/STATUS.md`](../../../docs/STATUS.md).
> La documentación completa anterior es recuperable desde Git en el commit `d2f6a27f`.

# Spec 027 — Platform Operations and Integrations

**Status:** IMPLEMENTATION_COMPLETE  
**API:** `/api/v1/platform-ops`

## Scope
Wraps existing platform/jobs and billing PaymentProvider. Console notification/email adapters (MOCK labeled). Webhook idempotency, jobs with retries/dead-letter, feature flags, health/metrics (academic), backup/restore verification (local). Secret redaction in API/UI.

## Tables (11)
`app_notification`, `app_notification_delivery`, `app_provider_configuration`, `app_webhook_event`, `app_webhook_delivery`, `app_background_job`, `app_job_execution`, `app_feature_flag`, `app_operational_incident`, `app_backup_record`, `app_restore_verification`.

## Permissions (platform)
`ops.view`, `ops.manage`, `ops.webhooks`, `ops.flags`

## Constraints
No production HA/email/backup claims. `secret_ref` only — no raw secrets. Reuses `AcademicMockProvider` from billing.
