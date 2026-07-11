# Audit Model — Spec 016

**Status**: DESIGN_APPROVED  
**Tabla:** `app_audit_log` · append-only · no editable por administrator org

## Campos

audit_id · organization_id? · actor_user_id · actor_platform_role? · action · target_type · target_id · previous_values (redact) · new_values (redact) · reason? · request_id · source · result · occurred_at

## Cobertura

organization · membership · invitation · role assign · permission matrix seed (platform) · context activate · elevated platform access · denials relevantes (result=denied)

## Reglas

- no tokens / passwords / secrets / invite plaintext  
- fallos auditables cuando seguridad lo requiera (denied elevated, cross-tenant probe opcional sampled)  
- elevated access **siempre** auditado con reason + expiración conceptual  
- administradores comunes: solo `audit.view` lectura  
