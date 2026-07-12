"""Spec 014 D1 — explicit API surface policy (documentation + helpers).

Canonical facade: ``/api/v1``.
V2 (``/api/v2``) and shadowed legacy handlers are compatibility adapters.

Registration order in ``main.py`` (enterprise before packages) is intentional for
overlapping paths; do not rely on order alone — document winners here.
"""

from __future__ import annotations

# method + path → classification
# Classifications: CANONICAL | COMPATIBILITY_ADAPTER | PUBLIC_INTENTIONAL |
# AUTH_REQUIRED | ADMIN_REQUIRED | ENGINEER_REQUIRED

ROUTE_POLICY: dict[str, str] = {
    # Public intentional
    "GET /health": "PUBLIC_INTENTIONAL",
    "GET /api/v1/health": "PUBLIC_INTENTIONAL",
    "GET /api/v1/users/auth-config": "PUBLIC_INTENTIONAL",
    "POST /api/v1/users/login": "PUBLIC_INTENTIONAL",
    "POST /api/v1/users/register": "PUBLIC_INTENTIONAL",
    "POST /api/v1/users/verify-email": "PUBLIC_INTENTIONAL",
    "POST /api/v1/users/resend-code": "PUBLIC_INTENTIONAL",
    "POST /api/v1/users/google": "PUBLIC_INTENTIONAL",
    "POST /api/v1/users/logout": "PUBLIC_INTENTIONAL",  # idempotent without token
    # Catalog reads (streaming UX; FE auth-guarded but API remains readable)
    "GET /api/v1/tracks": "PUBLIC_INTENTIONAL",
    "GET /api/v1/tracks/{id}": "PUBLIC_INTENTIONAL",
    "GET /api/v1/catalog/artists": "PUBLIC_INTENTIONAL",
    "GET /api/v1/artists": "AUTH_REQUIRED",
    "GET /api/v1/genres": "PUBLIC_INTENTIONAL",
    # Canonical enterprise contracts (FE ApiService)
    "GET /api/v1/dashboard/overview": "CANONICAL+AUTH_REQUIRED",
    "GET /api/v1/analytics/streams": "CANONICAL+AUTH_REQUIRED",
    "GET /api/v1/tracks/top": "CANONICAL+AUTH_REQUIRED",
    "GET /api/v1/tracks/recommendations/{user_id}": "CANONICAL+AUTH_REQUIRED",
    "GET /api/v1/users/{user_id}/insights": "CANONICAL+AUTH_REQUIRED",
    # Compatibility / modular
    "GET /api/v2/dashboard/*": "COMPATIBILITY_ADAPTER+AUTH_REQUIRED",
    "GET /api/v2/users/*": "COMPATIBILITY_ADAPTER+AUTH_REQUIRED",
    "GET /api/v2/analytics/*": "COMPATIBILITY_ADAPTER+AUTH_REQUIRED",
    "GET /api/v2/recommendations/{user_id}": "COMPATIBILITY_ADAPTER+AUTH_REQUIRED",
    # Engineer / admin
    "GET /api/v1/analytics/explorer/*": "ENGINEER_REQUIRED",
    "GET /api/v1/analytics/warehouse": "ENGINEER_REQUIRED",
    "POST /api/v1/stats/synthetic": "ENGINEER_REQUIRED",
    "GET /api/v1/stats/synthetic/limits": "ENGINEER_REQUIRED",
    "GET /api/v1/platform/status": "ENGINEER_REQUIRED",
    "GET /api/v1/stats/summary": "AUTH_REQUIRED",
    "POST /api/v1/ai/search/natural": "AUTH_REQUIRED",
}

# Explicit collision winners (method+path → canonical module)
COLLISION_WINNERS: dict[str, str] = {
    "GET /api/v1/dashboard/overview": "enterprise dashboards.router (packages streaming only has /dashboard/home)",
    "GET /api/v1/analytics/streams": "enterprise enterprise_analytics.router",
    "GET /api/v1/tracks/top": "enterprise tracks.router (packages streaming has no /top)",
    "GET /api/v1/users/{id}/insights": "enterprise enterprise_users.router",
}
