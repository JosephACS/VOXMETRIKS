"""Heuristics to identify synthetic pytest / Golden Path organizations.

Used by cleanup scripts and list filtering. Prefer slug patterns over display names.
Never treat the canonical enterprise demo slug as disposable test pollution.
"""

from __future__ import annotations

import re
from typing import Iterable

# Canonical demo — keep (seed) and never auto-delete as "test pollution".
CANONICAL_DEMO_SLUG = "enterprise-demo-s028"

# Exact slugs used by enterprise API / domain tests (stable).
EXACT_TEST_SLUGS = frozenset(
    {
        "api-acme",
        "life-api",
        "tenant-a",
        "tenant-b",
        "hdr-a",
        "inv-api",
        "xorg-a",
        "xorg-b",
        "billing-test-org-l3",
        "artists-test-org-m3",
        "catalog-rights-test-org-n3",
        "campaigns-test-org-o3",
        "biz-analytics-o3",
        "artists-sec-viewer-org-m5",
        "rights-sec-viewer-org-n5",
        "campaigns-viewer-o5",
        "compliance-viewer-q5",
        "compliance-api",
        "compliance-dsr",
        "reporting-api-org",
        "reporting-r2-org",
    }
)

_SLUG_PREFIXES = (
    "golden-path-s028-",
    "cs-org-",
    "test-org-",
)

_SLUG_SUBSTRINGS = (
    "-test-org-",
    "test-org-",
    "-sec-viewer-",
)

_NAME_EXACT = frozenset(
    {
        "api acme",
        "golden path s028 org",
        "artists test org m3",
        "billing test org l3",
        "catalog rights test org n3",
        "campaigns test org o3",
        "biz analytics o3",
        "campaigns viewer org",
        "compliance viewer",
    }
)

_NAME_RE = re.compile(
    r"(?i)\b(test org|sec viewer org|golden path s0\d+)\b"
)


def is_canonical_demo(slug: str | None) -> bool:
    return (slug or "").strip().lower() == CANONICAL_DEMO_SLUG


def looks_like_test_organization(
    *,
    slug: str,
    display_name: str = "",
    is_test: bool | None = None,
    is_demo: bool | None = None,
) -> bool:
    """Return True when the org is clearly from pytest / Golden Path / fixtures."""
    if is_test:
        return True
    s = (slug or "").strip().lower()
    n = (display_name or "").strip().lower()
    if not s:
        return False
    if is_canonical_demo(s) or is_demo:
        return False
    if s in EXACT_TEST_SLUGS:
        return True
    if any(s.startswith(p) for p in _SLUG_PREFIXES):
        return True
    if any(part in s for part in _SLUG_SUBSTRINGS):
        return True
    if n in _NAME_EXACT:
        return True
    if _NAME_RE.search(n) and ("test" in n or "golden path" in n or "viewer" in n):
        return True
    return False


def classify_org_row(row: dict) -> str:
    """Return 'demo' | 'test' | 'real' for reporting."""
    slug = str(row.get("slug") or "")
    if is_canonical_demo(slug) or bool(row.get("is_demo")):
        return "demo"
    if looks_like_test_organization(
        slug=slug,
        display_name=str(row.get("display_name") or ""),
        is_test=bool(row.get("is_test")),
        is_demo=bool(row.get("is_demo")),
    ):
        return "test"
    return "real"


def filter_visible_orgs(
    orgs: Iterable[dict],
    *,
    show_demo: bool,
) -> list[dict]:
    """Filter membership list for the org selector / list API."""
    out: list[dict] = []
    for o in orgs:
        kind = classify_org_row(o)
        if kind == "test":
            continue
        if kind == "demo" and not show_demo:
            continue
        out.append(o)
    return out
