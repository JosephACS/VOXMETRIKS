"""Royalties use cases — Spec 030.

Decimal money only. No universal artist %. Streams never become money
without an approved pool + attribution rule. B2B only via MANUAL_ATTRIBUTION.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.royalties.domain.errors import (
    B2BRequiresManualAttributionError,
    CurrencyMismatchError,
    InvalidTransitionError,
    NotFoundError,
    OwnershipSumError,
    PoolNotApprovedError,
    SettlementFinalizedError,
    SettlementNotApprovedError,
    StreamsWithoutPoolError,
    ValidationError,
)
from app.packages.royalties.domain.providers import (
    SimulatedPayoutProvider,
    SimulatedPayoutRequest,
)

MONEY_Q = Decimal("0.0001")
PART_Q = Decimal("0.00000001")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


def _dec(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return ZERO
    return Decimal(str(value))


def _money(value: Any) -> Decimal:
    return _dec(value).quantize(MONEY_Q, rounding=ROUND_HALF_UP)


def _part(value: Any) -> Decimal:
    return _dec(value).quantize(PART_Q, rounding=ROUND_HALF_UP)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _now() -> datetime:
    return utc_now()


def _table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [name],
    ).fetchone()
    return row is not None


def _row_to_dict(cols: tuple[str, ...], row: tuple) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i, c in enumerate(cols):
        v = row[i]
        if isinstance(v, float) and c.endswith(("_amount", "_total", "percentage", "participation")):
            v = _dec(v)
        elif c.endswith(("_amount", "_total")) or c in (
            "total_amount",
            "residual_amount",
            "gross_total",
            "adjustment_total",
            "net_total",
            "attributable_amount",
            "ownership_percentage",
            "gross_amount",
            "adjustment_amount",
            "net_amount",
            "participation",
            "amount",
        ):
            if v is not None:
                v = _dec(v)
        out[c] = v
    return out


_POOL_COLS = (
    "id", "organization_id", "currency", "period_start", "period_end", "status",
    "attribution_method", "total_amount", "residual_amount", "label", "is_demo",
    "idempotency_key", "created_by", "approved_by", "created_at", "updated_at", "approved_at",
)
_SOURCE_COLS = (
    "id", "pool_id", "source_kind", "source_payment_id", "source_invoice_id",
    "amount", "currency", "reason", "evidence_ref", "actor_user_id",
    "organization_id", "status", "created_at",
)
_RUN_COLS = (
    "id", "pool_id", "status", "currency", "gross_total", "adjustment_total",
    "net_total", "block_conflict_id", "idempotency_key", "created_by", "approved_by",
    "finalized_at", "created_at", "updated_at", "block_reason",
)
_ASSET_COLS = (
    "id", "settlement_run_id", "asset_id", "warehouse_track_id", "valid_event_count",
    "total_event_count", "participation", "attributable_amount", "rights_contract_id",
    "status", "block_reason", "created_at",
)
_PARTY_COLS = (
    "id", "settlement_run_id", "asset_allocation_id", "party_id", "party_name",
    "ownership_percentage", "gross_amount", "adjustment_amount", "net_amount",
    "rights_contract_id", "status", "created_at",
)
_STMT_COLS = (
    "id", "settlement_run_id", "party_id", "party_name", "period_start", "period_end",
    "currency", "gross_amount", "adjustment_amount", "net_amount", "status",
    "export_json", "created_at",
)
_BATCH_COLS = (
    "id", "settlement_run_id", "status", "currency", "total_amount",
    "idempotency_key", "created_by", "created_at", "updated_at",
)
_INSTR_COLS = (
    "id", "batch_id", "statement_id", "party_id", "amount", "currency",
    "destination_type", "destination_ref", "status", "idempotency_key",
    "created_at", "updated_at",
)


def _allocate_with_remainder(
    total: Decimal,
    items: list[tuple[Any, Decimal]],
    *,
    tie_keys: list[tuple],
) -> list[Decimal]:
    """Pro-rata money split; remainder to largest share (ties by tie_keys)."""
    if not items:
        return []
    total = _money(total)
    weights = [w for _, w in items]
    weight_sum = sum(weights, ZERO)
    if weight_sum <= ZERO:
        zeros = [ZERO] * len(items)
        if total != ZERO and items:
            # give all to first by tie order
            order = sorted(range(len(items)), key=lambda i: tie_keys[i])
            zeros[order[0]] = total
        return zeros

    raw = [total * (w / weight_sum) for w in weights]
    quantized = [_money(r) for r in raw]
    diff = _money(total - sum(quantized, ZERO))
    if diff != ZERO:
        # largest share first, then deterministic tie keys
        order = sorted(
            range(len(items)),
            key=lambda i: (-raw[i],) + tie_keys[i],
        )
        quantized[order[0]] = _money(quantized[order[0]] + diff)
    return quantized


class RoyaltiesUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._payout = SimulatedPayoutProvider()

    # ── Audit ──────────────────────────────────────────────────────────────

    def _audit(
        self,
        *,
        actor_user_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        organization_id: Optional[int] = None,
        detail: Optional[str] = None,
    ) -> None:
        aid = _next_id(self._conn, "app_royalty_audit_event")
        self._conn.execute(
            """
            INSERT INTO app_royalty_audit_event
                (id, organization_id, actor_user_id, action, entity_type, entity_id, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [aid, organization_id, actor_user_id, action, entity_type, entity_id, detail, _now()],
        )

    def _get_pool_row(self, pool_id: int) -> dict[str, Any]:
        cols = ", ".join(_POOL_COLS)
        row = self._conn.execute(
            f"SELECT {cols} FROM app_royalty_revenue_pool WHERE id = ?", [pool_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"Pool {pool_id} not found")
        return _row_to_dict(_POOL_COLS, row)

    def _get_run_row(self, run_id: int) -> dict[str, Any]:
        cols = ", ".join(_RUN_COLS)
        row = self._conn.execute(
            f"SELECT {cols} FROM app_royalty_settlement_run WHERE id = ?", [run_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"Settlement {run_id} not found")
        return _row_to_dict(_RUN_COLS, row)

    def _assert_not_finalized(self, run: dict[str, Any]) -> None:
        if run["status"] == "finalized":
            raise SettlementFinalizedError(
                f"Settlement {run['id']} is finalized and cannot be edited"
            )

    # ── Pool lifecycle ─────────────────────────────────────────────────────

    def create_pool(
        self,
        *,
        actor_user_id: int,
        currency: str,
        period_start: date,
        period_end: date,
        idempotency_key: str,
        attribution_method: str = "PRO_RATA_STREAM_SHARE",
        total_amount: Decimal = ZERO,
        label: Optional[str] = None,
        organization_id: Optional[int] = None,
        is_demo: bool = False,
    ) -> dict[str, Any]:
        currency = currency.strip().upper()
        if len(currency) != 3:
            raise ValidationError("currency must be ISO-4217 3-letter code")
        if attribution_method not in ("PRO_RATA_STREAM_SHARE", "MANUAL_ATTRIBUTION"):
            raise ValidationError(f"Invalid attribution_method={attribution_method}")
        if period_end < period_start:
            raise ValidationError("period_end must be >= period_start")

        existing = self._conn.execute(
            "SELECT id FROM app_royalty_revenue_pool WHERE idempotency_key = ?",
            [idempotency_key],
        ).fetchone()
        if existing:
            return self.get_pool(int(existing[0]))

        pid = _next_id(self._conn, "app_royalty_revenue_pool")
        now = _now()
        self._conn.execute(
            f"""
            INSERT INTO app_royalty_revenue_pool
                ({", ".join(_POOL_COLS)})
            VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, 0, ?, ?, ?, ?, NULL, ?, ?, NULL)
            """,
            [
                pid, organization_id, currency, period_start, period_end,
                attribution_method, _money(total_amount), label, is_demo,
                idempotency_key, actor_user_id, now, now,
            ],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="pool.create",
            entity_type="pool",
            entity_id=pid,
            organization_id=organization_id,
            detail=f"label={label} currency={currency}",
        )
        return self.get_pool(pid)

    def add_b2c_source(
        self,
        *,
        pool_id: int,
        actor_user_id: int,
        amount: Decimal,
        currency: str,
        source_payment_id: Optional[str] = None,
        source_invoice_id: Optional[str] = None,
        reason: Optional[str] = None,
        evidence_ref: Optional[str] = None,
        organization_id: Optional[int] = None,
        approve: bool = False,
        source_kind: str = "B2C_PERSONAL_PAYMENT",
    ) -> dict[str, Any]:
        if source_kind != "B2C_PERSONAL_PAYMENT":
            raise B2BRequiresManualAttributionError(
                "B2B income cannot be added as an automatic B2C source; "
                "use add_manual_b2b_source / MANUAL_ATTRIBUTION"
            )
        pool = self._get_pool_row(pool_id)
        if pool["status"] not in ("draft", "approved"):
            raise InvalidTransitionError(f"Cannot add source to pool status={pool['status']}")
        currency = currency.strip().upper()
        if currency != pool["currency"]:
            raise CurrencyMismatchError(
                f"Source currency {currency} != pool currency {pool['currency']}"
            )
        amount = _money(amount)
        if amount <= ZERO:
            raise ValidationError("amount must be > 0")

        sid = _next_id(self._conn, "app_royalty_revenue_source")
        status = "approved" if approve else "candidate"
        self._conn.execute(
            f"""
            INSERT INTO app_royalty_revenue_source
                ({", ".join(_SOURCE_COLS)})
            VALUES (?, ?, 'B2C_PERSONAL_PAYMENT', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                sid, pool_id, source_payment_id, source_invoice_id, amount, currency,
                reason, evidence_ref, actor_user_id, organization_id, status, _now(),
            ],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="source.add_b2c",
            entity_type="source",
            entity_id=sid,
            organization_id=organization_id or pool.get("organization_id"),
            detail=f"pool_id={pool_id} status={status} amount={amount}",
        )
        return self._get_source(sid)

    def add_manual_b2b_source(
        self,
        *,
        pool_id: int,
        actor_user_id: int,
        amount: Decimal,
        currency: str,
        reason: str,
        source_payment_id: Optional[str] = None,
        source_invoice_id: Optional[str] = None,
        evidence_ref: Optional[str] = None,
        organization_id: Optional[int] = None,
        approve: bool = True,
    ) -> dict[str, Any]:
        """Audited MANUAL_ATTRIBUTION path for B2B — never automatic."""
        if not reason or not reason.strip():
            raise ValidationError("MANUAL_ATTRIBUTION requires a non-empty reason")
        pool = self._get_pool_row(pool_id)
        if pool["status"] not in ("draft", "approved"):
            raise InvalidTransitionError(f"Cannot add source to pool status={pool['status']}")
        currency = currency.strip().upper()
        if currency != pool["currency"]:
            raise CurrencyMismatchError(
                f"Source currency {currency} != pool currency {pool['currency']}"
            )
        amount = _money(amount)
        if amount <= ZERO:
            raise ValidationError("amount must be > 0")

        sid = _next_id(self._conn, "app_royalty_revenue_source")
        status = "approved" if approve else "candidate"
        self._conn.execute(
            f"""
            INSERT INTO app_royalty_revenue_source
                ({", ".join(_SOURCE_COLS)})
            VALUES (?, ?, 'B2B_MANUAL', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                sid, pool_id, source_payment_id, source_invoice_id, amount, currency,
                reason.strip(), evidence_ref, actor_user_id, organization_id, status, _now(),
            ],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="source.manual_b2b",
            entity_type="source",
            entity_id=sid,
            organization_id=organization_id or pool.get("organization_id"),
            detail=f"pool_id={pool_id} MANUAL_ATTRIBUTION reason={reason.strip()}",
        )
        return self._get_source(sid)

    def _get_source(self, source_id: int) -> dict[str, Any]:
        cols = ", ".join(_SOURCE_COLS)
        row = self._conn.execute(
            f"SELECT {cols} FROM app_royalty_revenue_source WHERE id = ?", [source_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"Source {source_id} not found")
        return _row_to_dict(_SOURCE_COLS, row)

    def approve_pool(
        self,
        *,
        pool_id: int,
        actor_user_id: int,
        approve_candidate_b2c: bool = True,
    ) -> dict[str, Any]:
        pool = self._get_pool_row(pool_id)
        if pool["status"] != "draft":
            if pool["status"] == "approved":
                return pool
            raise InvalidTransitionError(f"Cannot approve pool status={pool['status']}")

        if approve_candidate_b2c:
            self._conn.execute(
                """
                UPDATE app_royalty_revenue_source
                SET status = 'approved'
                WHERE pool_id = ? AND source_kind = 'B2C_PERSONAL_PAYMENT' AND status = 'candidate'
                """,
                [pool_id],
            )

        approved_sum = self._conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM app_royalty_revenue_source
            WHERE pool_id = ? AND status = 'approved'
            """,
            [pool_id],
        ).fetchone()
        src_total = _money(approved_sum[0] if approved_sum else 0)
        total = src_total if src_total > ZERO else _money(pool["total_amount"])
        if total <= ZERO:
            raise ValidationError("Approved pool requires total_amount > 0 or approved sources")

        now = _now()
        self._conn.execute(
            """
            UPDATE app_royalty_revenue_pool
            SET status = 'approved', total_amount = ?, approved_by = ?, approved_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [total, actor_user_id, now, now, pool_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="pool.approve",
            entity_type="pool",
            entity_id=pool_id,
            organization_id=pool.get("organization_id"),
            detail=f"total_amount={total}",
        )
        return self.get_pool(pool_id)

    # ── Settlement calculation ─────────────────────────────────────────────

    def _load_stream_weights(
        self,
        pool: dict[str, Any],
        synthetic_event_counts: Optional[dict[int, int]] = None,
    ) -> dict[int, int]:
        """Return track_id -> event_count. Prefer warehouse, then demo table, then synthetic."""
        if synthetic_event_counts:
            return {int(k): int(v) for k, v in synthetic_event_counts.items() if int(v) > 0}

        demo_rows = self._conn.execute(
            """
            SELECT track_id, event_count FROM app_royalty_demo_stream_weight
            WHERE pool_id = ?
            """,
            [pool["id"]],
        ).fetchall()
        if demo_rows:
            return {int(r[0]): int(r[1]) for r in demo_rows}

        if _table_exists(self._conn, "fact_streaming"):
            # Prefer played_at / fecha_evento when present
            cols = {
                r[0]
                for r in self._conn.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'fact_streaming'"
                ).fetchall()
            }
            date_col = None
            if "played_at" in cols:
                date_col = "played_at"
            elif "fecha_evento" in cols:
                date_col = "fecha_evento"
            if "id_track" in cols:
                if date_col:
                    rows = self._conn.execute(
                        f"""
                        SELECT id_track, COUNT(*) AS cnt
                        FROM fact_streaming
                        WHERE CAST({date_col} AS DATE) >= ?
                          AND CAST({date_col} AS DATE) <= ?
                        GROUP BY id_track
                        """,
                        [pool["period_start"], pool["period_end"]],
                    ).fetchall()
                else:
                    rows = self._conn.execute(
                        "SELECT id_track, COUNT(*) AS cnt FROM fact_streaming GROUP BY id_track"
                    ).fetchall()
                return {int(r[0]): int(r[1]) for r in rows if r[0] is not None}

        raise StreamsWithoutPoolError(
            "No stream weights available (fact_streaming / demo weights / synthetic). "
            "Streams never become money without weights + approved pool + attribution."
        )

    def seed_demo_stream_weights(
        self,
        *,
        pool_id: int,
        weights: dict[int, int],
        is_synthetic: bool = True,
    ) -> int:
        self._get_pool_row(pool_id)
        n = 0
        for track_id, count in weights.items():
            if int(count) <= 0:
                continue
            wid = _next_id(self._conn, "app_royalty_demo_stream_weight")
            self._conn.execute(
                """
                INSERT INTO app_royalty_demo_stream_weight
                    (id, pool_id, track_id, event_count, is_synthetic)
                VALUES (?, ?, ?, ?, ?)
                """,
                [wid, pool_id, int(track_id), int(count), is_synthetic],
            )
            n += 1
        return n

    def calculate_pro_rata_settlement(
        self,
        *,
        pool_id: int,
        actor_user_id: int,
        idempotency_key: str,
        asset_scopes: Optional[list[dict[str, Any]]] = None,
        synthetic_event_counts: Optional[dict[int, int]] = None,
    ) -> dict[str, Any]:
        """Create settlement run and asset allocations by PRO_RATA stream share."""
        pool = self._get_pool_row(pool_id)
        if pool["status"] not in ("approved", "processing", "allocated"):
            raise PoolNotApprovedError(
                f"Pool {pool_id} must be approved before settlement (status={pool['status']})"
            )
        if pool["attribution_method"] != "PRO_RATA_STREAM_SHARE":
            raise ValidationError(
                "calculate_pro_rata_settlement requires attribution_method=PRO_RATA_STREAM_SHARE"
            )

        existing = self._conn.execute(
            "SELECT id FROM app_royalty_settlement_run WHERE idempotency_key = ?",
            [idempotency_key],
        ).fetchone()
        if existing:
            return self.get_settlement(int(existing[0]))

        weights = self._load_stream_weights(pool, synthetic_event_counts)
        total_events = sum(weights.values())
        if total_events <= 0:
            raise ValidationError("total stream events must be > 0")

        # Resolve asset scopes: provided or warehouse_track_id == track_id mapping
        scopes: list[dict[str, Any]] = list(asset_scopes or [])
        if not scopes:
            for track_id in weights:
                scopes.append(
                    {
                        "asset_id": int(track_id),
                        "warehouse_track_id": int(track_id),
                        "rights_contract_id": None,
                    }
                )

        track_to_scope = {}
        for s in scopes:
            tid = s.get("warehouse_track_id") or s.get("asset_id")
            if tid is not None:
                track_to_scope[int(tid)] = s

        # Only allocate for tracks that appear in both scopes and weights
        alloc_items: list[tuple[dict[str, Any], int]] = []
        for track_id, cnt in weights.items():
            scope = track_to_scope.get(int(track_id))
            if scope:
                alloc_items.append((scope, int(cnt)))

        if not alloc_items:
            raise ValidationError("No overlapping tracks between stream weights and asset_scopes")

        pool_total = _money(pool["total_amount"])
        participations = [
            _part(Decimal(cnt) / Decimal(total_events)) for _, cnt in alloc_items
        ]
        amounts = _allocate_with_remainder(
            pool_total,
            [(s, Decimal(cnt)) for s, cnt in alloc_items],
            tie_keys=[(int(s["asset_id"]),) for s, _ in alloc_items],
        )

        now = _now()
        run_id = _next_id(self._conn, "app_royalty_settlement_run")
        self._conn.execute(
            f"""
            INSERT INTO app_royalty_settlement_run
                ({", ".join(_RUN_COLS)})
            VALUES (?, ?, 'calculating', ?, ?, 0, ?, NULL, ?, ?, NULL, NULL, ?, ?, NULL)
            """,
            [
                run_id, pool_id, pool["currency"], pool_total, pool_total,
                idempotency_key, actor_user_id, now, now,
            ],
        )

        for i, (scope, cnt) in enumerate(alloc_items):
            aid = _next_id(self._conn, "app_royalty_asset_allocation")
            self._conn.execute(
                f"""
                INSERT INTO app_royalty_asset_allocation
                    ({", ".join(_ASSET_COLS)})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ok', NULL, ?)
                """,
                [
                    aid, run_id, int(scope["asset_id"]),
                    scope.get("warehouse_track_id"),
                    cnt, total_events, participations[i], amounts[i],
                    scope.get("rights_contract_id"), now,
                ],
            )

        # residual from pool.total - sum(alloc)
        allocated = _money(sum(amounts, ZERO))
        residual = _money(pool_total - allocated)
        self._conn.execute(
            "UPDATE app_royalty_revenue_pool SET residual_amount = ?, status = 'processing', updated_at = ? WHERE id = ?",
            [residual, now, pool_id],
        )
        self._conn.execute(
            "UPDATE app_royalty_settlement_run SET status = 'calculated', updated_at = ? WHERE id = ?",
            [now, run_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.pro_rata",
            entity_type="settlement",
            entity_id=run_id,
            organization_id=pool.get("organization_id"),
            detail=f"pool_id={pool_id} gross={pool_total}",
        )
        return self.get_settlement(run_id)

    def calculate_contract_splits(
        self,
        *,
        settlement_run_id: int,
        actor_user_id: int,
    ) -> dict[str, Any]:
        """Apply rights-contract ownership % to asset allocations. Sum must == 100."""
        run = self._get_run_row(settlement_run_id)
        self._assert_not_finalized(run)
        if run["status"] in ("blocked",):
            # still allow re-calc after fixing contracts? only from calculated/draft
            pass
        if run["status"] not in ("calculated", "draft", "calculating", "blocked", "under_review"):
            raise InvalidTransitionError(
                f"Cannot calculate splits for settlement status={run['status']}"
            )

        # Clear prior party allocations for re-run
        self._conn.execute(
            "DELETE FROM app_royalty_party_allocation WHERE settlement_run_id = ?",
            [settlement_run_id],
        )

        assets = self._conn.execute(
            f"SELECT {', '.join(_ASSET_COLS)} FROM app_royalty_asset_allocation "
            "WHERE settlement_run_id = ? ORDER BY asset_id",
            [settlement_run_id],
        ).fetchall()
        if not assets:
            raise ValidationError("No asset allocations to split")

        any_blocked = False
        block_conflict_id: Optional[int] = None
        block_reason: Optional[str] = None
        now = _now()
        pool = self._get_pool_row(int(run["pool_id"]))

        for arow in assets:
            asset = _row_to_dict(_ASSET_COLS, arow)
            contract_id = asset.get("rights_contract_id")
            if not contract_id:
                # try lookup by asset
                if _table_exists(self._conn, "app_rights_contract"):
                    crow = self._conn.execute(
                        """
                        SELECT id FROM app_rights_contract
                        WHERE asset_id = ? AND status = 'active'
                        ORDER BY id DESC LIMIT 1
                        """,
                        [asset["asset_id"]],
                    ).fetchone()
                    if crow:
                        contract_id = int(crow[0])
                        self._conn.execute(
                            "UPDATE app_royalty_asset_allocation SET rights_contract_id = ? WHERE id = ?",
                            [contract_id, asset["id"]],
                        )

            if not contract_id:
                any_blocked = True
                reason = f"No rights_contract for asset_id={asset['asset_id']}"
                block_reason = reason
                self._conn.execute(
                    "UPDATE app_royalty_asset_allocation SET status = 'blocked', block_reason = ? WHERE id = ?",
                    [reason, asset["id"]],
                )
                continue

            parties = self._conn.execute(
                """
                SELECT id, party_name, ownership_percentage
                FROM app_rights_contract_party
                WHERE contract_id = ?
                ORDER BY id
                """,
                [contract_id],
            ).fetchall()
            if not parties:
                any_blocked = True
                reason = f"No parties on rights_contract_id={contract_id}"
                block_reason = reason
                self._conn.execute(
                    "UPDATE app_royalty_asset_allocation SET status = 'blocked', block_reason = ? WHERE id = ?",
                    [reason, asset["id"]],
                )
                continue

            ownerships = [_money(p[2]) for p in parties]
            ownership_sum = _money(sum(ownerships, ZERO))
            if ownership_sum != HUNDRED:
                any_blocked = True
                reason = (
                    f"Ownership sum {ownership_sum} != 100 for contract_id={contract_id}"
                )
                block_reason = reason
                self._conn.execute(
                    "UPDATE app_royalty_asset_allocation SET status = 'blocked', block_reason = ? WHERE id = ?",
                    [reason, asset["id"]],
                )
                # optional rights conflict insert
                if _table_exists(self._conn, "app_rights_conflict"):
                    org_id = pool.get("organization_id") or 0
                    cid = _next_id(self._conn, "app_rights_conflict")
                    self._conn.execute(
                        """
                        INSERT INTO app_rights_conflict
                            (id, organization_id, asset_id, rights_type, territory_code,
                             status, details, resolved_by, resolved_at, created_at, updated_at)
                        VALUES (?, ?, ?, 'master', 'WW', 'open', ?, NULL, NULL, ?, ?)
                        """,
                        [cid, org_id, asset["asset_id"], reason, now, now],
                    )
                    block_conflict_id = cid
                continue

            attributable = _money(asset["attributable_amount"])
            party_amounts = _allocate_with_remainder(
                attributable,
                [(p, _dec(p[2])) for p in parties],
                tie_keys=[(int(asset["asset_id"]), int(p[0])) for p in parties],
            )
            self._conn.execute(
                "UPDATE app_royalty_asset_allocation SET status = 'ok', block_reason = NULL WHERE id = ?",
                [asset["id"]],
            )
            for i, p in enumerate(parties):
                paid = _next_id(self._conn, "app_royalty_party_allocation")
                gross = party_amounts[i]
                self._conn.execute(
                    f"""
                    INSERT INTO app_royalty_party_allocation
                        ({", ".join(_PARTY_COLS)})
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'ok', ?)
                    """,
                    [
                        paid, settlement_run_id, asset["id"], int(p[0]), p[1],
                        _money(p[2]), gross, gross, contract_id, now,
                    ],
                )

        if any_blocked:
            self._conn.execute(
                """
                UPDATE app_royalty_settlement_run
                SET status = 'blocked', block_conflict_id = ?, block_reason = ?, updated_at = ?
                WHERE id = ?
                """,
                [block_conflict_id, block_reason, now, settlement_run_id],
            )
            self._audit(
                actor_user_id=actor_user_id,
                action="settlement.blocked",
                entity_type="settlement",
                entity_id=settlement_run_id,
                organization_id=pool.get("organization_id"),
                detail=block_reason,
            )
            raise OwnershipSumError(block_reason or "Contract ownership blocked settlement")

        # recompute totals from party lines
        tot = self._conn.execute(
            """
            SELECT COALESCE(SUM(gross_amount), 0), COALESCE(SUM(adjustment_amount), 0),
                   COALESCE(SUM(net_amount), 0)
            FROM app_royalty_party_allocation WHERE settlement_run_id = ?
            """,
            [settlement_run_id],
        ).fetchone()
        gross, adj, net = _money(tot[0]), _money(tot[1]), _money(tot[2])
        self._conn.execute(
            """
            UPDATE app_royalty_settlement_run
            SET status = 'calculated', gross_total = ?, adjustment_total = ?, net_total = ?,
                block_conflict_id = NULL, block_reason = NULL, updated_at = ?
            WHERE id = ?
            """,
            [gross, adj, net, now, settlement_run_id],
        )
        self._conn.execute(
            "UPDATE app_royalty_revenue_pool SET status = 'allocated', updated_at = ? WHERE id = ?",
            [now, pool["id"]],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.contract_splits",
            entity_type="settlement",
            entity_id=settlement_run_id,
            organization_id=pool.get("organization_id"),
            detail=f"gross={gross} net={net}",
        )
        return self.get_settlement(settlement_run_id)

    def apply_adjustment(
        self,
        *,
        settlement_run_id: int,
        actor_user_id: int,
        amount: Decimal,
        reason: str,
        party_allocation_id: Optional[int] = None,
    ) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        self._assert_not_finalized(run)
        if run["status"] not in ("calculated", "under_review", "approved", "blocked"):
            raise InvalidTransitionError(f"Cannot adjust settlement status={run['status']}")
        if not reason or not reason.strip():
            raise ValidationError("adjustment reason required")
        amount = _money(amount)

        adj_id = _next_id(self._conn, "app_royalty_adjustment")
        now = _now()
        self._conn.execute(
            """
            INSERT INTO app_royalty_adjustment
                (id, settlement_run_id, party_allocation_id, amount, reason, actor_user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [adj_id, settlement_run_id, party_allocation_id, amount, reason.strip(), actor_user_id, now],
        )
        if party_allocation_id:
            prow = self._conn.execute(
                """
                SELECT gross_amount, adjustment_amount FROM app_royalty_party_allocation
                WHERE id = ? AND settlement_run_id = ?
                """,
                [party_allocation_id, settlement_run_id],
            ).fetchone()
            if not prow:
                raise NotFoundError(f"Party allocation {party_allocation_id} not found")
            new_adj = _money(_dec(prow[1]) + amount)
            new_net = _money(_dec(prow[0]) + new_adj)
            self._conn.execute(
                """
                UPDATE app_royalty_party_allocation
                SET adjustment_amount = ?, net_amount = ?
                WHERE id = ? AND settlement_run_id = ?
                """,
                [new_adj, new_net, party_allocation_id, settlement_run_id],
            )
        # refresh settlement totals
        tot = self._conn.execute(
            """
            SELECT COALESCE(SUM(gross_amount), 0), COALESCE(SUM(adjustment_amount), 0),
                   COALESCE(SUM(net_amount), 0)
            FROM app_royalty_party_allocation WHERE settlement_run_id = ?
            """,
            [settlement_run_id],
        ).fetchone()
        self._conn.execute(
            """
            UPDATE app_royalty_settlement_run
            SET gross_total = ?, adjustment_total = ?, net_total = ?, updated_at = ?
            WHERE id = ?
            """,
            [_money(tot[0]), _money(tot[1]), _money(tot[2]), now, settlement_run_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.adjustment",
            entity_type="adjustment",
            entity_id=adj_id,
            detail=f"amount={amount} reason={reason.strip()}",
        )
        return {"id": adj_id, "settlement_run_id": settlement_run_id, "amount": amount, "reason": reason.strip()}

    def generate_statements(
        self,
        *,
        settlement_run_id: int,
        actor_user_id: int,
    ) -> list[dict[str, Any]]:
        run = self._get_run_row(settlement_run_id)
        self._assert_not_finalized(run)
        if run["status"] not in ("calculated", "under_review", "approved"):
            raise InvalidTransitionError(
                f"Cannot generate statements for settlement status={run['status']}"
            )
        pool = self._get_pool_row(int(run["pool_id"]))

        # Aggregate by party across assets
        rows = self._conn.execute(
            """
            SELECT party_id, party_name,
                   SUM(gross_amount), SUM(adjustment_amount), SUM(net_amount)
            FROM app_royalty_party_allocation
            WHERE settlement_run_id = ? AND status = 'ok'
            GROUP BY party_id, party_name
            ORDER BY party_id
            """,
            [settlement_run_id],
        ).fetchall()
        if not rows:
            raise ValidationError("No party allocations to statement")

        # Replace prior drafts for re-run
        self._conn.execute(
            "DELETE FROM app_royalty_statement WHERE settlement_run_id = ? AND status = 'draft'",
            [settlement_run_id],
        )
        now = _now()
        out: list[dict[str, Any]] = []
        for r in rows:
            sid = _next_id(self._conn, "app_royalty_statement")
            export = json.dumps(
                {
                    "party_id": int(r[0]),
                    "party_name": r[1],
                    "gross": str(_money(r[2])),
                    "adjustment": str(_money(r[3])),
                    "net": str(_money(r[4])),
                    "simulated": True,
                }
            )
            self._conn.execute(
                f"""
                INSERT INTO app_royalty_statement
                    ({", ".join(_STMT_COLS)})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                """,
                [
                    sid, settlement_run_id, int(r[0]), r[1],
                    pool["period_start"], pool["period_end"], run["currency"],
                    _money(r[2]), _money(r[3]), _money(r[4]), export, now,
                ],
            )
            out.append(self._get_statement(sid))
        self._audit(
            actor_user_id=actor_user_id,
            action="statements.generate",
            entity_type="settlement",
            entity_id=settlement_run_id,
            organization_id=pool.get("organization_id"),
            detail=f"count={len(out)}",
        )
        return out

    def _get_statement(self, statement_id: int) -> dict[str, Any]:
        cols = ", ".join(_STMT_COLS)
        row = self._conn.execute(
            f"SELECT {cols} FROM app_royalty_statement WHERE id = ?", [statement_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"Statement {statement_id} not found")
        return _row_to_dict(_STMT_COLS, row)

    def submit_for_approval(
        self, *, settlement_run_id: int, actor_user_id: int
    ) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        self._assert_not_finalized(run)
        if run["status"] != "calculated":
            raise InvalidTransitionError(f"submit requires calculated, got {run['status']}")
        now = _now()
        self._conn.execute(
            "UPDATE app_royalty_settlement_run SET status = 'under_review', updated_at = ? WHERE id = ?",
            [now, settlement_run_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.submit",
            entity_type="settlement",
            entity_id=settlement_run_id,
        )
        return self.get_settlement(settlement_run_id)

    def approve_settlement(
        self, *, settlement_run_id: int, actor_user_id: int
    ) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        self._assert_not_finalized(run)
        if run["status"] not in ("under_review", "calculated"):
            raise InvalidTransitionError(f"Cannot approve settlement status={run['status']}")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_royalty_settlement_run
            SET status = 'approved', approved_by = ?, updated_at = ?
            WHERE id = ?
            """,
            [actor_user_id, now, settlement_run_id],
        )
        self._conn.execute(
            "UPDATE app_royalty_statement SET status = 'issued' WHERE settlement_run_id = ? AND status = 'draft'",
            [settlement_run_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.approve",
            entity_type="settlement",
            entity_id=settlement_run_id,
        )
        return self.get_settlement(settlement_run_id)

    def reject_settlement(
        self, *, settlement_run_id: int, actor_user_id: int, reason: str
    ) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        self._assert_not_finalized(run)
        if run["status"] not in ("under_review", "calculated", "approved"):
            raise InvalidTransitionError(f"Cannot reject settlement status={run['status']}")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_royalty_settlement_run
            SET status = 'blocked', block_reason = ?, updated_at = ?
            WHERE id = ?
            """,
            [reason or "rejected", now, settlement_run_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.reject",
            entity_type="settlement",
            entity_id=settlement_run_id,
            detail=reason,
        )
        return self.get_settlement(settlement_run_id)

    def finalize_settlement(
        self, *, settlement_run_id: int, actor_user_id: int
    ) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        if run["status"] == "finalized":
            return run
        if run["status"] != "approved":
            raise InvalidTransitionError(f"finalize requires approved, got {run['status']}")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_royalty_settlement_run
            SET status = 'finalized', finalized_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [now, now, settlement_run_id],
        )
        pool = self._get_pool_row(int(run["pool_id"]))
        self._conn.execute(
            "UPDATE app_royalty_revenue_pool SET status = 'closed', updated_at = ? WHERE id = ?",
            [now, pool["id"]],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="settlement.finalize",
            entity_type="settlement",
            entity_id=settlement_run_id,
            organization_id=pool.get("organization_id"),
        )
        return self.get_settlement(settlement_run_id)

    # ── Payouts (simulated only) ───────────────────────────────────────────

    def create_payout_batch(
        self,
        *,
        settlement_run_id: int,
        actor_user_id: int,
        idempotency_key: str,
        destination_type: str = "demo_wallet",
        destination_ref_prefix: str = "demo_wallet",
    ) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        if run["status"] not in ("approved", "finalized"):
            raise SettlementNotApprovedError(
                f"Payout requires approved/finalized settlement, got {run['status']}"
            )
        existing = self._conn.execute(
            "SELECT id FROM app_payout_batch WHERE idempotency_key = ?",
            [idempotency_key],
        ).fetchone()
        if existing:
            return self._get_batch(int(existing[0]))

        stmts = self._conn.execute(
            f"SELECT {', '.join(_STMT_COLS)} FROM app_royalty_statement "
            "WHERE settlement_run_id = ? AND net_amount > 0 ORDER BY party_id",
            [settlement_run_id],
        ).fetchall()
        if not stmts:
            raise ValidationError("No statements with positive net_amount for payout")

        now = _now()
        total = _money(sum((_money(s[9]) for s in stmts), ZERO))  # net_amount index
        batch_id = _next_id(self._conn, "app_payout_batch")
        self._conn.execute(
            f"""
            INSERT INTO app_payout_batch
                ({", ".join(_BATCH_COLS)})
            VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?)
            """,
            [
                batch_id, settlement_run_id, run["currency"], total,
                idempotency_key, actor_user_id, now, now,
            ],
        )
        for srow in stmts:
            stmt = _row_to_dict(_STMT_COLS, srow)
            iid = _next_id(self._conn, "app_payout_instruction")
            ikey = f"{idempotency_key}:party:{stmt['party_id']}"
            dest_ref = f"{destination_ref_prefix}:{stmt['party_id']}"
            self._conn.execute(
                f"""
                INSERT INTO app_payout_instruction
                    ({", ".join(_INSTR_COLS)})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                [
                    iid, batch_id, stmt["id"], stmt["party_id"],
                    _money(stmt["net_amount"]), run["currency"],
                    destination_type, dest_ref, ikey, now, now,
                ],
            )
        self._audit(
            actor_user_id=actor_user_id,
            action="payout.batch_create",
            entity_type="payout_batch",
            entity_id=batch_id,
            detail="simulated_only",
        )
        return self._get_batch(batch_id)

    def _get_batch(self, batch_id: int) -> dict[str, Any]:
        cols = ", ".join(_BATCH_COLS)
        row = self._conn.execute(
            f"SELECT {cols} FROM app_payout_batch WHERE id = ?", [batch_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"Payout batch {batch_id} not found")
        batch = _row_to_dict(_BATCH_COLS, row)
        instr = self._conn.execute(
            f"SELECT {', '.join(_INSTR_COLS)} FROM app_payout_instruction WHERE batch_id = ?",
            [batch_id],
        ).fetchall()
        batch["instructions"] = [_row_to_dict(_INSTR_COLS, r) for r in instr]
        return batch

    def simulate_payouts(
        self,
        *,
        batch_id: int,
        actor_user_id: int,
        scenario: str = "succeed",
    ) -> dict[str, Any]:
        batch = self._get_batch(batch_id)
        if batch["status"] in ("paid_simulated", "reversed"):
            return batch
        now = _now()
        self._conn.execute(
            "UPDATE app_payout_batch SET status = 'processing', updated_at = ? WHERE id = ?",
            [now, batch_id],
        )
        all_paid = True
        any_fail = False
        for instr in batch["instructions"]:
            if instr["status"] == "paid_simulated":
                continue
            result = self._payout.pay(
                SimulatedPayoutRequest(
                    amount=_money(instr["amount"]),
                    currency=instr["currency"],
                    idempotency_key=instr["idempotency_key"],
                    destination_type=instr["destination_type"],
                    destination_ref=instr["destination_ref"],
                    instruction_id=instr["id"],
                    scenario=scenario,
                )
            )
            self._conn.execute(
                "UPDATE app_payout_instruction SET status = ?, updated_at = ? WHERE id = ?",
                [result.status, now, instr["id"]],
            )
            eid = _next_id(self._conn, "app_payout_event")
            payload = json.dumps(
                {
                    "labeled_simulated": True,
                    "message": result.message,
                    "provider_ref": result.provider_ref,
                    "scenario": result.scenario,
                    "error_code": result.error_code,
                }
            )
            self._conn.execute(
                """
                INSERT INTO app_payout_event (id, instruction_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [eid, instr["id"], f"payout.{result.status}", payload, now],
            )
            if not result.success or result.status == "failed":
                any_fail = True
                all_paid = False
                fid = _next_id(self._conn, "app_payout_failure")
                self._conn.execute(
                    """
                    INSERT INTO app_payout_failure
                        (id, instruction_id, failure_code, message, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        fid, instr["id"],
                        result.error_code or "simulated_failure",
                        result.message, now,
                    ],
                )
            elif result.status != "paid_simulated":
                all_paid = False

        final_status = "paid_simulated" if all_paid else ("failed" if any_fail else "processing")
        if scenario == "reversed":
            final_status = "reversed"
        self._conn.execute(
            "UPDATE app_payout_batch SET status = ?, updated_at = ? WHERE id = ?",
            [final_status, now, batch_id],
        )
        if final_status == "paid_simulated":
            self._conn.execute(
                """
                UPDATE app_royalty_statement SET status = 'paid_simulated'
                WHERE id IN (SELECT statement_id FROM app_payout_instruction WHERE batch_id = ?)
                """,
                [batch_id],
            )
        self._audit(
            actor_user_id=actor_user_id,
            action="payout.simulate",
            entity_type="payout_batch",
            entity_id=batch_id,
            detail=f"scenario={scenario} status={final_status}",
        )
        return self._get_batch(batch_id)

    def retry_payout(
        self,
        *,
        instruction_id: int,
        actor_user_id: int,
        scenario: str = "succeed",
    ) -> dict[str, Any]:
        cols = ", ".join(_INSTR_COLS)
        row = self._conn.execute(
            f"SELECT {cols} FROM app_payout_instruction WHERE id = ?", [instruction_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"Instruction {instruction_id} not found")
        instr = _row_to_dict(_INSTR_COLS, row)
        if instr["status"] not in ("failed", "processing"):
            raise InvalidTransitionError(f"Cannot retry instruction status={instr['status']}")
        # New idempotency key for retry attempt but store event against instruction
        retry_key = f"{instr['idempotency_key']}:retry:{_next_id(self._conn, 'app_payout_event')}"
        result = self._payout.pay(
            SimulatedPayoutRequest(
                amount=_money(instr["amount"]),
                currency=instr["currency"],
                idempotency_key=retry_key,
                destination_type=instr["destination_type"],
                destination_ref=instr["destination_ref"],
                instruction_id=instruction_id,
                scenario=scenario,
            )
        )
        now = _now()
        self._conn.execute(
            "UPDATE app_payout_instruction SET status = ?, updated_at = ? WHERE id = ?",
            [result.status, now, instruction_id],
        )
        eid = _next_id(self._conn, "app_payout_event")
        self._conn.execute(
            """
            INSERT INTO app_payout_event (id, instruction_id, event_type, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                eid, instruction_id, f"payout.retry.{result.status}",
                json.dumps({"labeled_simulated": True, "message": result.message}),
                now,
            ],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="payout.retry",
            entity_type="payout_instruction",
            entity_id=instruction_id,
            detail=result.message,
        )
        return self._get_batch(int(instr["batch_id"]))

    def reverse_payout(
        self, *, batch_id: int, actor_user_id: int
    ) -> dict[str, Any]:
        batch = self._get_batch(batch_id)
        if batch["status"] not in ("paid_simulated", "processing", "approved"):
            raise InvalidTransitionError(f"Cannot reverse batch status={batch['status']}")
        now = _now()
        for instr in batch["instructions"]:
            result = self._payout.pay(
                SimulatedPayoutRequest(
                    amount=_money(instr["amount"]),
                    currency=instr["currency"],
                    idempotency_key=f"{instr['idempotency_key']}:reverse",
                    destination_type=instr["destination_type"],
                    destination_ref=instr["destination_ref"],
                    instruction_id=instr["id"],
                    scenario="reversed",
                )
            )
            self._conn.execute(
                "UPDATE app_payout_instruction SET status = ?, updated_at = ? WHERE id = ?",
                [result.status, now, instr["id"]],
            )
            eid = _next_id(self._conn, "app_payout_event")
            self._conn.execute(
                """
                INSERT INTO app_payout_event (id, instruction_id, event_type, payload, created_at)
                VALUES (?, ?, 'payout.reversed', ?, ?)
                """,
                [
                    eid, instr["id"],
                    json.dumps({"labeled_simulated": True, "message": result.message}),
                    now,
                ],
            )
        self._conn.execute(
            "UPDATE app_payout_batch SET status = 'reversed', updated_at = ? WHERE id = ?",
            [now, batch_id],
        )
        self._audit(
            actor_user_id=actor_user_id,
            action="payout.reverse",
            entity_type="payout_batch",
            entity_id=batch_id,
            detail="[SIMULATED] reversed",
        )
        return self._get_batch(batch_id)

    # ── Reads / metrics ────────────────────────────────────────────────────

    def metrics_dashboard(
        self, *, organization_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Income vs pool totals are separate fields — never equated."""
        params: list[Any] = []
        org_filter = ""
        if organization_id is not None:
            org_filter = " AND organization_id = ?"
            params.append(organization_id)

        pools = self._conn.execute(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN status = 'approved' THEN total_amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status IN ('allocated','closed') THEN total_amount ELSE 0 END), 0),
                COUNT(*)
            FROM app_royalty_revenue_pool
            WHERE 1=1 {org_filter.replace('organization_id', 'organization_id')}
            """,
            params,
        ).fetchone()
        settlements = self._conn.execute(
            """
            SELECT
                COALESCE(SUM(gross_total), 0),
                COALESCE(SUM(net_total), 0),
                COUNT(*)
            FROM app_royalty_settlement_run
            """
        ).fetchone()
        payouts = self._conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN status = 'paid_simulated' THEN total_amount ELSE 0 END), 0),
                COUNT(*)
            FROM app_payout_batch
            """
        ).fetchone()
        return {
            "income_note": "Platform B2C/B2B income is NOT equal to distributable pool",
            "distributable_pool_approved": _money(pools[0]),
            "distributable_pool_allocated_or_closed": _money(pools[1]),
            "pool_count": int(pools[2]),
            "settlement_gross_total": _money(settlements[0]),
            "settlement_net_total": _money(settlements[1]),
            "settlement_count": int(settlements[2]),
            "payout_paid_simulated_total": _money(payouts[0]),
            "payout_batch_count": int(payouts[1]),
            "simulated_only": True,
        }

    def get_pool(self, pool_id: int) -> dict[str, Any]:
        pool = self._get_pool_row(pool_id)
        src = self._conn.execute(
            f"SELECT {', '.join(_SOURCE_COLS)} FROM app_royalty_revenue_source WHERE pool_id = ?",
            [pool_id],
        ).fetchall()
        pool["sources"] = [_row_to_dict(_SOURCE_COLS, r) for r in src]
        return pool

    def list_pools(
        self, *, organization_id: Optional[int] = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        if organization_id is not None:
            rows = self._conn.execute(
                f"SELECT {', '.join(_POOL_COLS)} FROM app_royalty_revenue_pool "
                "WHERE organization_id = ? OR organization_id IS NULL "
                "ORDER BY id DESC LIMIT ? OFFSET ?",
                [organization_id, limit, offset],
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT {', '.join(_POOL_COLS)} FROM app_royalty_revenue_pool "
                "ORDER BY id DESC LIMIT ? OFFSET ?",
                [limit, offset],
            ).fetchall()
        return [_row_to_dict(_POOL_COLS, r) for r in rows]

    def get_settlement(self, settlement_run_id: int) -> dict[str, Any]:
        run = self._get_run_row(settlement_run_id)
        assets = self._conn.execute(
            f"SELECT {', '.join(_ASSET_COLS)} FROM app_royalty_asset_allocation "
            "WHERE settlement_run_id = ? ORDER BY asset_id",
            [settlement_run_id],
        ).fetchall()
        parties = self._conn.execute(
            f"SELECT {', '.join(_PARTY_COLS)} FROM app_royalty_party_allocation "
            "WHERE settlement_run_id = ? ORDER BY party_id, asset_allocation_id",
            [settlement_run_id],
        ).fetchall()
        run["asset_allocations"] = [_row_to_dict(_ASSET_COLS, r) for r in assets]
        run["party_allocations"] = [_row_to_dict(_PARTY_COLS, r) for r in parties]
        return run

    def list_statements(
        self, *, settlement_run_id: Optional[int] = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        if settlement_run_id is not None:
            rows = self._conn.execute(
                f"SELECT {', '.join(_STMT_COLS)} FROM app_royalty_statement "
                "WHERE settlement_run_id = ? ORDER BY party_id LIMIT ? OFFSET ?",
                [settlement_run_id, limit, offset],
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT {', '.join(_STMT_COLS)} FROM app_royalty_statement "
                "ORDER BY id DESC LIMIT ? OFFSET ?",
                [limit, offset],
            ).fetchall()
        return [_row_to_dict(_STMT_COLS, r) for r in rows]
