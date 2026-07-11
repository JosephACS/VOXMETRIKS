# Legal, Security and Compliance Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11  

**No afirma** cumplimiento GDPR, PCI, ISO, SRI ni legislación específica.

---

## Alcance

Diseñar controles y procesos; **no** certificar ni declarar readiness legal/regulatoria.

---

## Temas diseñados

| Tema | Diseño |
|------|--------|
| Consentimiento | `consent_record` por finalidad |
| Términos | Aceptación versionada en signup/checkout |
| Acceso sensible | Roles + audit + justificación cross-org temporal |
| Incidente | Proceso L; MTTR medido como KPI propuesto |
| DSR / eliminación | Flujos con retención **configurable** (plazos no afirmados como ley) |
| Auditoría | Append-only lógico; rol `auditor` |

---

## Audio y límites

| Afirmación | Estado |
|------------|--------|
| Resolución técnica YT/Audius/demo | **Parcial** (código actual) |
| Derechos comerciales de catálogo tipo Spotify | **No** afirmados |
| Servicio de streaming licenciado | **Fuera de alcance** hasta evidencia |
| Uso académico/demo | **Uso limitado a demostración académica; permisos, licencias y cumplimiento de términos del proveedor no verificados.** |

---

## Pagos / datos de tarjeta

- No almacenar PAN/CVV.  
- Solo `payment_method_reference` / tokens.  
- Mock académico **no** implica readiness PCI.  
- **No** se afirma cumplimiento PCI-DSS.

---

## Autenticación actual (honestidad técnica)

El sistema actual usa **autenticación y sesiones bearer** (evidencia de sesión/`app_session` y flujos de auth del backend).  
**No** se afirma en este documento que el mecanismo sea JWT salvo evidencia explícita adicional fuera de esta corrección.

Transición futura: org-scoped RBAC, consentimientos, DSR formales = **diseñado**.

---

## Prohibiciones documentales

- No declarar “cumplimos GDPR/PCI/ISO/SRI”.  
- No inventar auditorías pasadas.  
- No presentar audio demo como licencia verificada.  
- No ocultar que términos de proveedores de audio **no están verificados**.
