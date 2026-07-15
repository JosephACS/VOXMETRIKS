"""Tests — matriz ligera de precios canónicos y permisos publishing/royalty."""

from __future__ import annotations

from decimal import Decimal

from app.packages.organizations.infrastructure.catalogs import ROLE_PERMISSION_MATRIX
from app.packages.personal_subscriptions.application.catalog import PERSONAL_CATALOG
from app.packages.subscriptions.application.commercial_catalog import COMMERCIAL_CATALOG


def test_b2c_canonical_prices():
    by_code = {p.code: p for p in PERSONAL_CATALOG}
    free_amounts = [p.amount for p in by_code["personal_free"].prices]
    assert Decimal("0.00") in free_amounts
    ind = {p.billing_period: p.amount for p in by_code["premium_individual"].prices}
    assert ind["monthly"] == Decimal("4.99")
    assert ind["annual"] == Decimal("49.90")
    duo = {p.billing_period: p.amount for p in by_code["premium_duo"].prices}
    assert duo["monthly"] == Decimal("7.99") and duo["annual"] == Decimal("79.90")
    fam = {p.billing_period: p.amount for p in by_code["premium_family"].prices}
    assert fam["monthly"] == Decimal("9.99") and fam["annual"] == Decimal("99.90")


def test_b2b_canonical_prices():
    by = {p.code: p for p in COMMERCIAL_CATALOG}
    starter = {p.billing_period: p.amount for p in by["starter"].prices}
    assert starter["monthly"] == Decimal("49.00") and starter["annual"] == Decimal("490.00")
    assert {p.billing_period: p.amount for p in by["professional"].prices}["monthly"] == Decimal("99.00")
    assert {p.billing_period: p.amount for p in by["business"].prices}["monthly"] == Decimal("199.00")
    assert {p.billing_period: p.amount for p in by["enterprise"].prices}["monthly"] == Decimal("499.00")


def test_finance_has_no_publishing_approve():
    perms = ROLE_PERMISSION_MATRIX.get("finance", frozenset())
    assert "publishing.publish" not in perms
    assert "publishing.review" not in perms


def test_billing_manager_has_royalty_view():
    perms = ROLE_PERMISSION_MATRIX.get("billing_manager", frozenset())
    assert "royalty.view" in perms
    assert "publishing.publish" not in perms


def test_artist_manager_cannot_payout():
    perms = ROLE_PERMISSION_MATRIX.get("artist_manager", frozenset())
    assert "royalty.payout" not in perms
