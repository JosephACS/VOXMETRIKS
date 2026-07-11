# Contact and Prospect Model — Spec 017

**Status**: DESIGN_APPROVED · IMPLEMENTATION_PENDING

---

## Prospect

### Propósito
Lead / cuenta potencial **antes** de ser organización cliente.

### Campos conceptuales
`prospect_id` · `display_name` · `legal_name_declared?` · `source` · `status` · `owner_user_id` (sales_agent) · `organization_id?` (null pre-conversión) · `disqualify_reason?` · `notes_summary?` · timestamps · `created_by`

### Estados
`lead` | `new` | `contacted` | `qualified` | `disqualified` | `converted`

**Nota HUM003:** unificar `lead`≡`new` en implementación; hasta entonces ambos documentados como equivalentes de entrada.

### Transiciones (resumen)
Ver `lifecycle-state-machines.md` § Prospect.

### Reglas
| ID | Regla |
|----|-------|
| BR-PRO-01 | Platform-scoped hasta conversión |
| BR-PRO-02 | Solo roles sales_*/platform_admin/auditor (view) |
| BR-PRO-03 | Convert solo vía path opportunity won + contract accepted + conversion |
| BR-PRO-04 | Disqualify exige razón |
| BR-PRO-05 | Reopen disqualified → requiere sales_manager |
| BR-PRO-06 | Duplicados: detectar por criterios; **no** merge automático dudoso |

### Detección de duplicados (diseño)
Criterios sugeridos (configurables): email de contacto primary normalizado; `display_name`+país; dominio email corporativo.  
Acción: flag `possible_duplicate_of` / cola revisión — **no** fusión silenciosa.

### Sensibilidad / retención
PII comercial media; retención comercial; no afirmar consentimiento legal sin registro.

---

## Contact

### Propósito
Persona de la cuenta prospecto. **No** es `app_user` automáticamente.

### Campos
`contact_id` · `full_name` · `email` · `phone?` · `job_title?` · `declared_company?` · `is_primary` · `is_decision_maker` · `is_authorized_signatory` · `contact_preference?` · `consent_recorded` (bool) · `consent_recorded_at?` · `consent_basis_note?` · `linked_user_id?` (opcional, solo si ya existe identity) · timestamps

### Relación N:N
`crm_prospect_contact`: prospect_id + contact_id + role_flags + valid_from/to.

### Reglas
| ID | Regla |
|----|-------|
| BR-CON-01 | Crear contacto ≠ crear usuario |
| BR-CON-02 | No afirmar consentimiento si `consent_recorded=false` |
| BR-CON-03 | Al menos un primary por prospect activo (recomendado; soft rule) |
| BR-CON-04 | Authorized signatory requerido antes de accept contract (hard en conversión) |
| BR-CON-05 | Email normalizado para match duplicados; conflicto → revisión |

### Participantes externos (conceptuales, no roles RBAC)
- prospect contact  
- decision maker  
- authorized signatory  

---

## KPI / proceso
Proceso A sales-assisted · KPI prospects created · qualification rate.
