# API contracts — Spec 030

Base: `/api/v1/royalties`

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | /pools | royalty.view | Lists pools; income vs distributable fields separate |
| POST | /pools | royalty.manage | Create draft pool |
| GET | /pools/{id} | royalty.view | |
| POST | /pools/{id}/approve | royalty.approve_pool | draft → approved |
| GET | /pools/{id}/contribution-candidates | royalty.view | B2C settled defaults; B2B excluded |
| POST | /pools/{id}/contributions/approve | royalty.approve_pool | Approve B2C candidates |
| POST | /pools/{id}/manual-attributions | royalty.manage | B2B (or exception) MANUAL_ATTRIBUTION audited |
| GET | /pools/{id}/attribution-rules | royalty.view | |
| POST | /pools/{id}/attribution-rules | royalty.manage | PRO_RATA_STREAM_SHARE \| MANUAL_ATTRIBUTION |
| POST | /pools/{id}/settle | royalty.settle | Requires approved pool + rule + 100% ownership |
| GET | /settlements/{id} | royalty.view | |
| GET | /settlements/{id}/lines | royalty.view | Statement lines Decimal |
| POST | /settlements/{id}/simulate-payout | royalty.simulate_payout | Simulated only |
| GET | /simulated-payouts/{id} | royalty.view | |
| GET | /admin/metrics | ops.view / royalty.view | Labeled income ≠ pool totals |
| POST | /admin/demo-seed | ops.manage | Opt-in demo |

## Error highlights

| Code / condition | When |
|------------------|------|
| 409 / `OwnershipSumError` | Parties ≠ 100% |
| 409 / `PoolNotApproved` | Settle on draft |
| 409 / `B2BRequiresManualAttribution` | B2B auto-feed attempted |
| 409 / `StreamsWithoutRule` | Streams used without attribution rule |
| 200 idempotent | Duplicate settle / simulate `idempotency_key` |

Billing and personal payment APIs remain under `/api/v1` billing + `/api/v1/personal`.
