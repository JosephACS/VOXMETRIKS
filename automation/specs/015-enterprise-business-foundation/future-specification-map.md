# Future Specification Map — Spec 015

**Status**: Diseñado — **sin números definitivos** · **sin crear carpetas**  
**Fecha**: 2026-07-11

---

## Principio

015 es la **fundación documental**. La implementación se parte en specs posteriores autorizadas una a una. Los títulos siguientes son **temas**, no IDs.

---

## Temas propuestos (orden recomendado)

| Orden | Tema | Depende de | Entrega principal |
|------:|------|------------|-------------------|
| 1 | Enterprise identity and organizations | 015, identity actual | Org, members, invites, RBAC org-scoped |
| 2 | CRM and commercial contracting | 1 | Prospect→contract |
| 3 | Plans and subscriptions | 1 | plan, subscription, add-ons, entitlements |
| 4 | Billing, payments and reconciliation | 3 | invoices, PaymentProvider mock→real, mora |
| 5 | Artists and team management | 1 | artist_profile, assignments |
| 6 | Catalog rights and contracts | 5 | rights, territories, disputes |
| 7 | Campaigns, budgets and approvals | 1, 6 | campaign cycle + approvals |
| 8 | Engagement and business analytics | engagement/analytics actuales + 1 | KPIs org-scoped, joins seguros |
| 9 | Executive reporting and decisions | 8, 4 (agg), 7 | reports, business_decision |
| 10 | Customer success and support | 1, 3 | health, tickets, onboarding |
| 11 | Compliance, privacy and audit | 1 | consent, DSR, retention, audit UX |
| 12 | Platform operations and integrations | transversal | providers, webhooks, ops hardening |

---

## Dependencias (diagrama)

```text
[015 Foundation]
    → (1) Identity & Organizations
        → (2) CRM & Contracts
        → (3) Plans & Subscriptions → (4) Billing & Payments
        → (5) Artists → (6) Catalog Rights → (7) Campaigns
        → (10) CS & Support
        → (11) Compliance
    → (8) Engagement & Business Analytics → (9) Reporting & Decisions
    → (12) Platform Ops (continuo)
```

---

## Qué no hacer todavía

- Asignar `016`, `017`, … hasta autorización.
- Crear directorios `automation/specs/016-...`.
- Implementar en paralelo dominios sin org tenancy (1).

---

## Relación con deudas 014

Las deudas aceptadas de 014 (Docker, Playwright, shims, ELT backend, playback-core, etc.) **no** se “arreglan” dentro de 015. Pueden aparecer como tareas en (12) u otras specs técnicas explícitas, separadas del business foundation.
