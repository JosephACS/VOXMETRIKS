"""Shared organization profile catalogs (Spec 053).

Server-owned type/country/timezone/currency catalogs and country defaults.
"""

from __future__ import annotations

from typing import Final, Optional

# (code, label)
ORGANIZATION_TYPES: Final[tuple[tuple[str, str], ...]] = (
    ("label", "Sello"),
    ("distributor", "Distribuidor"),
    ("publisher", "Editora"),
    ("management", "Management"),
    ("other", "Otra"),
)

# Accepted by create/update but not offered in the public Spec 053 catalog UI.
LEGACY_ORGANIZATION_TYPES: Final[frozenset[str]] = frozenset({"prospect"})

ORGANIZATION_TYPE_CODES: Final[frozenset[str]] = (
    frozenset(c for c, _ in ORGANIZATION_TYPES) | LEGACY_ORGANIZATION_TYPES
)

COUNTRIES: Final[tuple[tuple[str, str], ...]] = (
    ("EC", "Ecuador"),
    ("MX", "México"),
    ("CO", "Colombia"),
    ("PE", "Perú"),
    ("CL", "Chile"),
    ("AR", "Argentina"),
    ("ES", "España"),
    ("US", "Estados Unidos"),
)

TIMEZONES: Final[tuple[tuple[str, str], ...]] = (
    ("America/Guayaquil", "America/Guayaquil"),
    ("America/Bogota", "America/Bogota"),
    ("America/Mexico_City", "America/Mexico_City"),
    ("America/Lima", "America/Lima"),
    ("America/Santiago", "America/Santiago"),
    ("America/Argentina/Buenos_Aires", "America/Argentina/Buenos_Aires"),
    ("Europe/Madrid", "Europe/Madrid"),
    ("UTC", "UTC"),
)

CURRENCIES: Final[tuple[tuple[str, str], ...]] = (
    ("USD", "USD"),
    ("EUR", "EUR"),
    ("MXN", "MXN"),
    ("COP", "COP"),
    ("PEN", "PEN"),
    ("CLP", "CLP"),
    ("ARS", "ARS"),
)

# Country → (timezone, currency)
COUNTRY_DEFAULTS: Final[dict[str, tuple[str, str]]] = {
    "EC": ("America/Guayaquil", "USD"),
    "MX": ("America/Mexico_City", "MXN"),
    "CO": ("America/Bogota", "COP"),
    "PE": ("America/Lima", "PEN"),
    "CL": ("America/Santiago", "CLP"),
    "AR": ("America/Argentina/Buenos_Aires", "ARS"),
    "ES": ("Europe/Madrid", "EUR"),
    "US": ("UTC", "USD"),
}

COUNTRY_CODES: Final[frozenset[str]] = frozenset(c for c, _ in COUNTRIES)
TIMEZONE_CODES: Final[frozenset[str]] = frozenset(c for c, _ in TIMEZONES)
CURRENCY_CODES: Final[frozenset[str]] = frozenset(c for c, _ in CURRENCIES)

# Roles that may be offered on invitations (never owner / platform-only).
INVITATION_SAFE_ROLE_CODES: Final[frozenset[str]] = frozenset(
    {
        "administrator",
        "billing_manager",
        "finance",
        "artist_manager",
        "marketing_manager",
        "analyst",
        "artist",
        "viewer",
        "auditor",
        "customer_success_manager",
        "support_agent",
        "catalog_reviewer",
    }
)

MEMBERSHIP_STATUS_LABELS: Final[dict[str, str]] = {
    "active": "Activo",
    "suspended": "Suspendido",
    "left": "Salió",
    "removed": "Eliminado",
}


def defaults_for_country(country_code: Optional[str]) -> tuple[str, str]:
    code = (country_code or "").strip().upper()
    if code in COUNTRY_DEFAULTS:
        return COUNTRY_DEFAULTS[code]
    return ("UTC", "USD")


def validate_organization_type(value: str) -> str:
    code = (value or "").strip().lower()
    if code not in ORGANIZATION_TYPE_CODES:
        raise ValueError("invalid_catalog_value")
    return code


def validate_country_code(value: Optional[str]) -> Optional[str]:
    if value is None or not str(value).strip():
        return None
    code = str(value).strip().upper()
    if code not in COUNTRY_CODES:
        raise ValueError("invalid_catalog_value")
    return code


def validate_timezone(value: str) -> str:
    code = (value or "").strip()
    if code not in TIMEZONE_CODES:
        raise ValueError("invalid_catalog_value")
    return code


def validate_currency(value: str) -> str:
    code = (value or "").strip().upper()
    if code not in CURRENCY_CODES:
        raise ValueError("invalid_catalog_value")
    return code


def catalogs_payload() -> dict:
    return {
        "organization_types": [{"code": c, "label": l} for c, l in ORGANIZATION_TYPES],
        "countries": [{"code": c, "label": l} for c, l in COUNTRIES],
        "timezones": [{"code": c, "label": l} for c, l in TIMEZONES],
        "currencies": [{"code": c, "label": l} for c, l in CURRENCIES],
    }
