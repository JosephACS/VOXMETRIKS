# Data Ownership Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  
**Sin migraciones DuckDB.** Un solo dominio propietario por entidad.

**Scope:** `platform` = sin/org antes de conversión o datos de operador; `organization` = tenancy cliente.

---

## identity

### user
| Campo | Valor |
|-------|-------|
| Dominio propietario | identity |
| Propósito | Persona autenticable |
| ID | user_id (UUID) |
| Scope | platform |
| Campos | email, status, profile_name, created_at |
| Relaciones | sessions; organization_members |
| Estados | active/disabled (auth) |
| Auditoría | cambios de credencial/status |
| Retención | política cuenta |
| Sensibilidad | alta (PII) |
| Reutilización actual | **Sí parcial** — `app_user` |
| KPI/proceso | login; A-alt; B |

### session
| Campo | Valor |
|-------|-------|
| Dominio | identity |
| Propósito | Sesión bearer actual |
| ID | session_id |
| Scope | platform |
| Campos | user_id, expires_at, revoked |
| Relaciones | user |
| Estados | active/revoked/expired |
| Auditoría | create/revoke |
| Retención | corta |
| Sensibilidad | alta |
| Reutilización | **Sí parcial** — `app_session` |
| KPI/proceso | auth |

### credential
| Campo | Valor |
|-------|-------|
| Dominio | identity |
| Propósito | Secreto de autenticación (hash) |
| ID | credential_id |
| Scope | platform |
| Campos | user_id, password_hash, algo, rotated_at |
| Relaciones | user |
| Estados | active/rotated |
| Auditoría | rotate |
| Retención | mientras cuenta |
| Sensibilidad | crítica |
| Reutilización | **Parcial** (auth actual) |
| KPI/proceso | login |

### permission
| Campo | Valor |
|-------|-------|
| Dominio | identity |
| Propósito | Catálogo global de códigos de permiso |
| ID | permission_code |
| Scope | platform |
| Campos | code, description |
| Relaciones | usadas por role assignments (organizations) |
| Estados | n/a |
| Auditoría | cambios de catálogo |
| Retención | indefinida diseño |
| Sensibilidad | baja |
| Reutilización | **No** (roles técnicos distintos) |
| KPI/proceso | RBAC |

---

## organizations

### organization
| Campo | Valor |
|-------|-------|
| Dominio | organizations |
| Propósito | Cuenta B2B |
| ID | organization_id |
| Scope | organization (self) |
| Campos | name, status, created_at |
| Relaciones | members, invitations, subscriptions (ref), artists |
| Estados | provisioning, active, suspended_by_platform, closed |
| Auditoría | status changes |
| Retención | contractual |
| Sensibilidad | media |
| Reutilización | **No** |
| KPI/proceso | B; KPI orgs_active |

### organization_member
| Campo | Valor |
|-------|-------|
| Dominio | organizations |
| Propósito | Vínculo user↔org |
| ID | membership_id |
| Scope | organization |
| Campos | organization_id, user_id, status |
| Relaciones | role assignments |
| Estados | invited/active/suspended/removed |
| Auditoría | sí |
| Retención | membresía |
| Sensibilidad | media |
| Reutilización | **No** (app_user ≠ membership) |
| KPI/proceso | B |

### invitation
| Campo | Valor |
|-------|-------|
| Dominio | organizations |
| Propósito | Invite a org |
| ID | invitation_id |
| Scope | organization |
| Campos | org_id, email, token_ref, expires_at, roles_proposed |
| Relaciones | organization |
| Estados | pending, accepted, expired, revoked |
| Auditoría | sí |
| Retención | corta post-accept |
| Sensibilidad | media (email) |
| Reutilización | **No** |
| KPI/proceso | B |

### business_role (assignment)
| Campo | Valor |
|-------|-------|
| Dominio | organizations |
| Propósito | Asignación de rol org a membership |
| ID | role_assignment_id |
| Scope | organization |
| Campos | membership_id, role_code, granted_by |
| Relaciones | permission codes (identity catalog) |
| Estados | active/revoked |
| Auditoría | sí |
| Retención | mientras membership |
| Sensibilidad | media |
| Reutilización | **No** |
| KPI/proceso | B; least privilege |

---

## crm (platform-scoped pre-conversión)

### prospect
| Campo | Valor |
|-------|-------|
| Dominio | crm |
| Propósito | Lead temprano |
| ID | prospect_id |
| Scope | platform (org_id null hasta convert) |
| Campos | name, email, source, status, organization_id? |
| Relaciones | opportunities |
| Estados | new…converted |
| Auditoría | sí |
| Retención | comercial |
| Sensibilidad | media |
| Reutilización | **No** |
| KPI/proceso | A |

### opportunity
| Campo | Valor |
|-------|-------|
| Dominio | crm |
| Propósito | Negocio calificado |
| ID | opportunity_id |
| Scope | platform → +organization_id post |
| Campos | prospect_id, amount_estimate, currency, status, lose_reason |
| Relaciones | quotations |
| Estados | open, negotiation, won, lost |
| Auditoría | sí |
| Retención | comercial |
| Sensibilidad | media |
| Reutilización | **No** |
| KPI/proceso | A; pipeline KPIs |

### quotation
| Campo | Valor |
|-------|-------|
| Dominio | crm |
| Propósito | Oferta plan/precio/add-ons |
| ID | quotation_id |
| Scope | platform |
| Campos | opportunity_id, lines, currency, valid_until, discount |
| Relaciones | commercial_contract |
| Estados | draft…expired |
| Auditoría | sí |
| Retención | comercial |
| Sensibilidad | media |
| Reutilización | **No** |
| KPI/proceso | A |

---

## contracts

### commercial_contract
| Campo | Valor |
|-------|-------|
| Dominio | contracts |
| Propósito | Términos comerciales firmados |
| ID | contract_id |
| Scope | platform + organization_id post-firma |
| Campos | quotation_id, terms_ref, signed_at, status |
| Relaciones | organization |
| Estados | draft…terminated |
| Auditoría | sí |
| Retención | larga |
| Sensibilidad | alta |
| Reutilización | **No** |
| KPI/proceso | A; win contracts |

---

## subscriptions

### plan
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Producto vendible |
| ID | plan_id |
| Scope | platform |
| Campos | name, status |
| Relaciones | plan_price, plan_feature |
| Estados | draft/published/retired |
| Auditoría | sí |
| Retención | catálogo |
| Sensibilidad | baja |
| Reutilización actual | **No** |
| KPI/proceso | C |

### plan_price
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Precio configurable (no definitivo) |
| ID | plan_price_id |
| Scope | platform |
| Campos | plan_id, currency, interval, amount |
| Relaciones | plan |
| Estados | active/retired |
| Auditoría | sí |
| Retención | catálogo |
| Sensibilidad | baja |
| Reutilización actual | **No** |
| KPI/proceso | C; MRR |

### plan_feature
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Feature incluida en plan |
| ID | plan_feature_id |
| Scope | platform |
| Campos | plan_id, feature_code, limit |
| Relaciones | subscription_entitlement |
| Estados | n/a |
| Auditoría | sí |
| Retención | catálogo |
| Sensibilidad | baja |
| Reutilización actual | **No** |
| KPI/proceso | C |

### addon
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Complemento vendible |
| ID | addon_id |
| Scope | platform |
| Campos | code, price_ref, feature_code |
| Relaciones | subscription_change |
| Estados | active/retired |
| Auditoría | sí |
| Retención | catálogo |
| Sensibilidad | baja |
| Reutilización actual | **No** |
| KPI/proceso | C |

### subscription
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Ciclo de suscripción de la org |
| ID | subscription_id |
| Scope | organization |
| Campos | org_id, plan_id, status, billing_currency, period_start/end |
| Relaciones | changes, entitlements, usage |
| Estados | trialing, active, past_due, canceled, expired |
| Auditoría | sí |
| Retención | financiera/comercial |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | C; SaaS KPIs |

### subscription_change
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Historial de cambios |
| ID | change_id |
| Scope | organization |
| Campos | subscription_id, type, from/to, reason |
| Relaciones | subscription |
| Estados | applied |
| Auditoría | sí |
| Retención | historial |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | C |

### subscription_entitlement
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Derecho de uso efectivo (input de access) |
| ID | entitlement_id |
| Scope | organization |
| Campos | subscription_id, feature_code, limit, access_state |
| Relaciones | subscription |
| Estados | refleja access full/limited/blocked |
| Auditoría | cambios por orquestación |
| Retención | mientras sub activa |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | C, E |
| Motivo de inclusión | Separar entitlements del cobro |

### usage_record
| Campo | Valor |
|-------|-------|
| Dominio propietario | subscriptions |
| Propósito | Consumo medible |
| ID | usage_id |
| Scope | organization |
| Campos | subscription_id, metric, quantity, at |
| Relaciones | subscription |
| Estados | recorded |
| Auditoría | append-only |
| Retención | según plan |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | C; adopción |

---

## billing

### billing_profile
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Datos fiscales de cobro |
| ID | billing_profile_id |
| Scope | organization |
| Campos | legal_name, tax_id, address, currency_default |
| Relaciones | org, invoices |
| Estados | complete/incomplete |
| Auditoría | sí |
| Retención | fiscal |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | D |

### invoice
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Documento de cobro (una moneda) |
| ID | invoice_id |
| Scope | organization |
| Campos | org_id, currency, due_at, status, totals |
| Relaciones | items, allocations |
| Estados | draft…credited |
| Auditoría | sí |
| Retención | fiscal |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | D |

### invoice_item
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Línea de factura |
| ID | invoice_item_id |
| Scope | organization |
| Campos | invoice_id, description, amount, tax_config_ref |
| Relaciones | invoice |
| Estados | n/a |
| Auditoría | con invoice |
| Retención | fiscal |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | D |

### payment_method_reference
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Referencia tokenizada (sin PAN/CVV) |
| ID | pm_ref_id |
| Scope | organization |
| Campos | provider, token, brand, last4?, exp_month/year? |
| Relaciones | org |
| Estados | active/removed |
| Auditoría | sí |
| Retención | mientras método |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | E |

### payment_attempt
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Intento hacia proveedor |
| ID | payment_attempt_id |
| Scope | organization |
| Campos | idempotency_key, amount, currency, status, invoice_id? |
| Relaciones | payment?, provider_events |
| Estados | created, processing, succeeded, failed, canceled |
| Auditoría | sí |
| Retención | financiera |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | E |

### payment
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Pago tras attempt exitoso |
| ID | payment_id |
| Scope | organization |
| Campos | attempt_id, amount, currency, status |
| Relaciones | allocations, refunds |
| Estados | recorded/authorized…reversed |
| Auditoría | sí |
| Retención | financiera |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | E |

### payment_allocation
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Aplicar pago a factura(s) |
| ID | allocation_id |
| Scope | organization |
| Campos | payment_id, invoice_id, amount |
| Relaciones | payment, invoice |
| Estados | applied |
| Auditoría | sí |
| Retención | financiera |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | E |
| Motivo de inclusión | Pagos parciales explícitos |

### refund
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Devolución de payment |
| ID | refund_id |
| Scope | organization |
| Campos | payment_id, amount, status |
| Relaciones | payment, ledger |
| Estados | requested…completed |
| Auditoría | sí |
| Retención | financiera |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | E |

### credit_note
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Nota de crédito sobre invoice |
| ID | credit_note_id |
| Scope | organization |
| Campos | invoice_id, amount, reason, status |
| Relaciones | invoice, ledger |
| Estados | issued/applied |
| Auditoría | sí |
| Retención | fiscal |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | D |

### payment_provider_event
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Evento proveedor idempotente |
| ID | provider_event_id (único) |
| Scope | platform/organization |
| Campos | provider, signature_ok, payload_ref, processed_at |
| Relaciones | attempts/payments |
| Estados | received/processed/ignored_duplicate |
| Auditoría | sí |
| Retención | financiera |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | E |
| Motivo de inclusión | Webhooks sin doble cobro |

### billing_ledger_entry
| Campo | Valor |
|-------|-------|
| Dominio propietario | billing |
| Propósito | Asiento append-only |
| ID | ledger_entry_id |
| Scope | organization |
| Campos | account, debit/credit, amount, currency, ref_type/id |
| Relaciones | invoice/payment/refund/credit |
| Estados | posted |
| Auditoría | inmutable |
| Retención | financiera |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | D/E |
| Motivo de inclusión | No edición destructiva |

---

## artists / catalog_rights

### artist_profile
| Campo | Valor |
|-------|-------|
| Dominio propietario | artists |
| Propósito | Artista de negocio |
| ID | artist_profile_id |
| Scope | organization |
| Campos | name, status, warehouse_artist_ref? |
| Relaciones | assignments, rights |
| Estados | draft…archived |
| Auditoría | sí |
| Retención | negocio |
| Sensibilidad | media |
| Reutilización actual | ref opcional `dim_artista` |
| KPI/proceso | F |

### artist_assignment
| Campo | Valor |
|-------|-------|
| Dominio propietario | artists |
| Propósito | Manager/equipo |
| ID | assignment_id |
| Scope | organization |
| Campos | artist_id, user_id, role |
| Relaciones | artist, member |
| Estados | active/ended |
| Auditoría | sí |
| Retención | negocio |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | F |

### catalog_ownership
| Campo | Valor |
|-------|-------|
| Dominio propietario | catalog_rights |
| Propósito | Vínculo asset↔org/artist |
| ID | catalog_ownership_id |
| Scope | organization |
| Campos | asset_id, artist_id?, warehouse_track_ref? |
| Relaciones | rights_contracts |
| Estados | active |
| Auditoría | sí |
| Retención | derechos |
| Sensibilidad | media |
| Reutilización actual | ref opcional dim_track |
| KPI/proceso | G |

### rights_contract
| Campo | Valor |
|-------|-------|
| Dominio propietario | catalog_rights |
| Propósito | Contrato de derechos |
| ID | rights_contract_id |
| Scope | organization |
| Campos | asset_id, rights_type, exclusive, authorized_use, valid_from, valid_to, status |
| Relaciones | parties, territories |
| Estados | draft…disputed |
| Auditoría | sí |
| Retención | larga |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | G |

### contract_party
| Campo | Valor |
|-------|-------|
| Dominio propietario | catalog_rights |
| Propósito | Parte y % |
| ID | contract_party_id |
| Scope | organization |
| Campos | rights_contract_id, party_name, ownership_percentage |
| Relaciones | rights_contract |
| Estados | n/a |
| Auditoría | sí |
| Retención | con contrato |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | G |
| Validación | % por asset+rights_type+territory+periodo |

### territory
| Campo | Valor |
|-------|-------|
| Dominio propietario | catalog_rights |
| Propósito | Ámbito territorial |
| ID | territory_id / code |
| Scope | platform (+ uso org) |
| Campos | code, name |
| Relaciones | rights_contract |
| Estados | n/a |
| Auditoría | catálogo |
| Retención | catálogo |
| Sensibilidad | baja |
| Reutilización actual | **No** |
| KPI/proceso | G |

---

## campaigns

### campaign
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Campaña marketing |
| ID | campaign_id |
| Scope | organization |
| Campos | objective, artist_id?, status, market, segment |
| Relaciones | budget, expenses, results |
| Estados | draft…canceled |
| Auditoría | sí |
| Retención | marketing |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | H |

### campaign_budget
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Presupuesto |
| ID | budget_id |
| Scope | organization |
| Campos | campaign_id, amount, currency |
| Relaciones | approvals |
| Estados | draft/approved |
| Auditoría | sí |
| Retención | marketing |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | H |

### campaign_approval
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Aprobación presupuesto |
| ID | campaign_approval_id |
| Scope | organization |
| Campos | budget_id, status, approver |
| Relaciones | approval machine |
| Estados | pending… |
| Auditoría | sí |
| Retención | marketing |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | H |

### campaign_expense
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Gasto ejecutado |
| ID | expense_id |
| Scope | organization |
| Campos | campaign_id, amount, currency, at |
| Relaciones | campaign |
| Estados | recorded |
| Auditoría | sí |
| Retención | marketing |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | H |

### campaign_result
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Resultado operativo |
| ID | result_id |
| Scope | organization |
| Campos | campaign_id, metrics_json, goal_attainment |
| Relaciones | campaign |
| Estados | recorded |
| Auditoría | sí |
| Retención | marketing |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | H |

### attribution_definition
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Reglas versionadas de atribución |
| ID | attribution_definition_id |
| Scope | organization o template platform |
| Campos | version, rules, confidence_policy, owner |
| Relaciones | attributable_revenue_record |
| Estados | active/retired |
| Auditoría | sí |
| Retención | metodología |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | H ROI |
| Motivo de inclusión | ROI no sin definición |

### attributable_revenue_record
| Campo | Valor |
|-------|-------|
| Dominio propietario | campaigns |
| Propósito | Ingreso atribuible aprobado |
| ID | attr_rev_id |
| Scope | organization |
| Campos | campaign_id, attribution_definition_id, amount, currency, period, confidence, approved_by |
| Relaciones | campaign |
| Estados | draft/approved |
| Auditoría | sí |
| Retención | marketing/finance |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | H |
| Motivo de inclusión | Fuente de ingreso explícita |

---

## support / CS / reporting / platform / compliance

### support_case
| Campo | Valor |
|-------|-------|
| Dominio propietario | support |
| Propósito | Ticket |
| ID | case_id |
| Scope | organization o platform |
| Campos | subject, priority, status |
| Relaciones | messages |
| Estados | ticket machine |
| Auditoría | sí |
| Retención | soporte |
| Sensibilidad | media-alta |
| Reutilización actual | **No** |
| KPI/proceso | K |

### support_message
| Campo | Valor |
|-------|-------|
| Dominio propietario | support |
| Propósito | Mensaje de caso |
| ID | message_id |
| Scope | con case |
| Campos | case_id, author, body |
| Relaciones | case |
| Estados | n/a |
| Auditoría | sí |
| Retención | con case |
| Sensibilidad | media-alta |
| Reutilización actual | **No** |
| KPI/proceso | K |

### customer_health_snapshot
| Campo | Valor |
|-------|-------|
| Dominio propietario | customer_success |
| Propósito | Health puntual |
| ID | snapshot_id |
| Scope | organization |
| Campos | score_state, components, at |
| Relaciones | org |
| Estados | healthy…critical |
| Auditoría | sí |
| Retención | CS |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | J |

### onboarding_step
| Campo | Valor |
|-------|-------|
| Dominio propietario | customer_success |
| Propósito | Paso onboarding |
| ID | step_id |
| Scope | organization |
| Campos | code, status, completed_at |
| Relaciones | org |
| Estados | pending/done/skipped |
| Auditoría | sí |
| Retención | CS |
| Sensibilidad | baja |
| Reutilización actual | **No** |
| KPI/proceso | J |

### executive_report
| Campo | Valor |
|-------|-------|
| Dominio propietario | reporting |
| Propósito | Reporte ejecutivo |
| ID | report_id |
| Scope | organization/platform |
| Campos | type, status, period |
| Relaciones | decisions |
| Estados | report machine |
| Auditoría | sí |
| Retención | reporting |
| Sensibilidad | media |
| Reutilización actual | **No** (≠ dashboards actuales) |
| KPI/proceso | I |

### business_decision
| Campo | Valor |
|-------|-------|
| Dominio propietario | reporting |
| Propósito | Decisión registrada |
| ID | decision_id |
| Scope | organization/platform |
| Campos | proposal, status, evidence_refs |
| Relaciones | report |
| Estados | decision machine |
| Auditoría | sí |
| Retención | dirección |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | golden path decisión |

### business_event
| Campo | Valor |
|-------|-------|
| Dominio propietario | platform |
| Propósito | Evento de integración |
| ID | event_id |
| Scope | platform |
| Campos | type, payload_ref, correlation_id |
| Relaciones | consumidores |
| Estados | published |
| Auditoría | bus |
| Retención | ops |
| Sensibilidad | variable |
| Reutilización actual | **Parcial** logs |
| KPI/proceso | transversal |

### audit_log
| Campo | Valor |
|-------|-------|
| Dominio propietario | compliance |
| Propósito | Traza de auditoría |
| ID | audit_id |
| Scope | platform/organization |
| Campos | actor, action, entity, before/after |
| Relaciones | — |
| Estados | appended |
| Auditoría | self |
| Retención | compliance |
| Sensibilidad | alta |
| Reutilización actual | **Parcial** posible |
| KPI/proceso | L |

### notification
| Campo | Valor |
|-------|-------|
| Dominio propietario | platform |
| Propósito | Aviso usuario |
| ID | notification_id |
| Scope | user/org |
| Campos | channel, template, status |
| Relaciones | user |
| Estados | queued/sent/failed |
| Auditoría | sí |
| Retención | corta |
| Sensibilidad | media |
| Reutilización actual | **No** |
| KPI/proceso | transversal |

### consent_record
| Campo | Valor |
|-------|-------|
| Dominio propietario | compliance |
| Propósito | Consentimiento |
| ID | consent_id |
| Scope | user/org |
| Campos | purpose, version, granted_at, revoked_at |
| Relaciones | user |
| Estados | granted/revoked |
| Auditoría | sí |
| Retención | compliance |
| Sensibilidad | alta |
| Reutilización actual | **No** |
| KPI/proceso | L |

---

## Entidades añadidas (esta corrección)

| Entidad | Motivo |
|---------|--------|
| subscription_entitlement | Separar acceso/features del cobro |
| payment_provider_event | Idempotencia webhook / firma |
| payment_allocation | Pagos parciales explícitos |
| billing_ledger_entry | Ledger no destructivo |
| attribution_definition | ROI con metodología versionada |
| attributable_revenue_record | Fuente de ingreso aprobada |

## Dependencia circular eliminada

`subscriptions ↔ billing` reemplazada por **eventos + orquestación** (ver `domain-boundaries.md`).
