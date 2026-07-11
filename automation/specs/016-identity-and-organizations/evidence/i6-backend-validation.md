# I6 — Backend validation

**Status**: PASS  
**Date**: 2026-07-11

## Suites Organizations (I1–I5)

| Suite | Result |
|-------|--------|
| domain I2 | PASS (included) |
| schema/repositories I1 | PASS (included) |
| use cases I2 | PASS (included) |
| API/context I3 | PASS (included) |
| security I5 | PASS (included) |
| **Org suites total** | **63 collected / 63 PASS** |

Artifact: `evidence/_i6_org_suites.txt`

## Pytest completo

| Métrica | Valor |
|---------|------:|
| Collected | **231** |
| Passed | **231** |
| Failed | **0** |
| Skipped | **0** (ninguno reportado) |

Artifact: `evidence/_i6_pytest_full.txt`

## Startup / health / auth smoke

TestClient startup OK (warehouse_ready, org schema ensured).

| Check | Result |
|-------|--------|
| GET `/api/v1/health` | **200** |
| POST login demo | **200** |
| GET `/me` | **200** |
| GET `/organizations/current` | **200** (`context=active`) |
| GET `/organizations` | **200** (`n=9` for demo on warehouse used by smoke) |
| POST logout | **200** |
| GET `/me` after logout | **401** |

Artifact: `evidence/_i6_auth_smoke.txt`  
Note: smoke resolved to main warehouse path at runtime (settings); no org create/delete performed.

## Warnings

Ningún warning de pytest ocultado. Logs de boot INFO normales.
