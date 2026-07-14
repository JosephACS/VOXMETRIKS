"""Unit tests for test-org detection heuristics (cleanup / selector)."""

from app.packages.organizations.domain.test_org_patterns import (
    CANONICAL_DEMO_SLUG,
    classify_org_row,
    looks_like_test_organization,
    looks_like_test_plan,
)


def test_other_org_uuid_suffix_is_test():
    assert looks_like_test_organization(
        slug="other-org-1bfcfdf6",
        display_name="Other Org 1bfcfdf6",
    )


def test_canonical_demo_never_test():
    assert not looks_like_test_organization(
        slug=CANONICAL_DEMO_SLUG,
        display_name="VOXMETRIKS Demo",
        is_demo=True,
    )
    assert classify_org_row(
        {"slug": CANONICAL_DEMO_SLUG, "display_name": "VOXMETRIKS Demo", "is_demo": True}
    ) == "demo"


def test_legacy_demo_slug_protected():
    assert not looks_like_test_organization(
        slug="enterprise-demo-s028",
        display_name="Enterprise Demo Org (Synthetic)",
        is_demo=True,
    )


def test_exact_api_acme():
    assert looks_like_test_organization(slug="api-acme", display_name="API Acme")


def test_test_plan_detection():
    assert looks_like_test_plan(code="gp-plan", display_name="GP Plan")
    assert looks_like_test_plan(code="k3-test-plan", display_name="K3 Test Plan")
    assert not looks_like_test_plan(code="professional", display_name="Professional")
