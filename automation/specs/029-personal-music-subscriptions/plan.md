# Plan — Spec 029

## Approach

Additive DuckDB schema `personal_*` packages under `apps/backend/app/packages/personal_subscriptions/`.  
Reuse mock payment patterns; do **not** alter `app_subscription` / org billing uniqueness rules.

## Workstreams

1. Schema + catalog + use cases + entitlements  
2. Hook verify/login → Free  
3. Playlist/favorite gates  
4. HTTP `/api/v1/personal/*`  
5. Frontend `/account/*`  
6. Demo seed + metrics  
7. Tests + docs + TRACEABILITY  

## Out of scope

- Real card vaulting  
- Real SMTP in pytest  
- Changing B2B plan codes/prices  
