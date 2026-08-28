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
    ("AR", "Argentina"),
    ("BO", "Bolivia"),
    ("BR", "Brasil"),
    ("CL", "Chile"),
    ("CO", "Colombia"),
    ("CR", "Costa Rica"),
    ("DO", "República Dominicana"),
    ("SV", "El Salvador"),
    ("GT", "Guatemala"),
    ("HN", "Honduras"),
    ("MX", "México"),
    ("NI", "Nicaragua"),
    ("PA", "Panamá"),
    ("PY", "Paraguay"),
    ("PE", "Perú"),
    ("PR", "Puerto Rico"),
    ("UY", "Uruguay"),
    ("VE", "Venezuela"),
    ("CA", "Canadá"),
    ("US", "Estados Unidos"),
    ("ES", "España"),
    ("PT", "Portugal"),
    ("GB", "Reino Unido"),
    ("FR", "Francia"),
    ("DE", "Alemania"),
    ("IT", "Italia"),
    ("NL", "Países Bajos"),
    ("BE", "Bélgica"),
    ("CH", "Suiza"),
    ("IE", "Irlanda"),
    ("AU", "Australia"),
    ("NZ", "Nueva Zelanda"),
    ("JP", "Japón"),
    ("KR", "Corea del Sur"),
    ("IN", "India"),
)

TIMEZONES: Final[tuple[tuple[str, str], ...]] = (
    ("America/Guayaquil", "America/Guayaquil"),
    ("America/Argentina/Buenos_Aires", "America/Argentina/Buenos_Aires"),
    ("America/La_Paz", "America/La_Paz"),
    ("America/Sao_Paulo", "America/Sao_Paulo"),
    ("America/Santiago", "America/Santiago"),
    ("America/Bogota", "America/Bogota"),
    ("America/Costa_Rica", "America/Costa_Rica"),
    ("America/Santo_Domingo", "America/Santo_Domingo"),
    ("America/El_Salvador", "America/El_Salvador"),
    ("America/Guatemala", "America/Guatemala"),
    ("America/Tegucigalpa", "America/Tegucigalpa"),
    ("America/Mexico_City", "America/Mexico_City"),
    ("America/Managua", "America/Managua"),
    ("America/Panama", "America/Panama"),
    ("America/Asuncion", "America/Asuncion"),
    ("America/Lima", "America/Lima"),
    ("America/Puerto_Rico", "America/Puerto_Rico"),
    ("America/Montevideo", "America/Montevideo"),
    ("America/Caracas", "America/Caracas"),
    ("America/New_York", "America/New_York"),
    ("America/Toronto", "America/Toronto"),
    ("Europe/Madrid", "Europe/Madrid"),
    ("Europe/Lisbon", "Europe/Lisbon"),
    ("Europe/London", "Europe/London"),
    ("Europe/Paris", "Europe/Paris"),
    ("Europe/Berlin", "Europe/Berlin"),
    ("Europe/Rome", "Europe/Rome"),
    ("Europe/Amsterdam", "Europe/Amsterdam"),
    ("Europe/Brussels", "Europe/Brussels"),
    ("Europe/Zurich", "Europe/Zurich"),
    ("Europe/Dublin", "Europe/Dublin"),
    ("Australia/Sydney", "Australia/Sydney"),
    ("Pacific/Auckland", "Pacific/Auckland"),
    ("Asia/Tokyo", "Asia/Tokyo"),
    ("Asia/Seoul", "Asia/Seoul"),
    ("Asia/Kolkata", "Asia/Kolkata"),
    ("UTC", "UTC"),
)

CURRENCIES: Final[tuple[tuple[str, str], ...]] = (
    ("USD", "USD"),
    ("ARS", "ARS"),
    ("BOB", "BOB"),
    ("BRL", "BRL"),
    ("CLP", "CLP"),
    ("COP", "COP"),
    ("CRC", "CRC"),
    ("DOP", "DOP"),
    ("GTQ", "GTQ"),
    ("HNL", "HNL"),
    ("MXN", "MXN"),
    ("NIO", "NIO"),
    ("PYG", "PYG"),
    ("PEN", "PEN"),
    ("UYU", "UYU"),
    ("VES", "VES"),
    ("CAD", "CAD"),
    ("EUR", "EUR"),
    ("GBP", "GBP"),
    ("CHF", "CHF"),
    ("AUD", "AUD"),
    ("NZD", "NZD"),
    ("JPY", "JPY"),
    ("KRW", "KRW"),
    ("INR", "INR"),
)

# Country → (timezone, currency)
COUNTRY_DEFAULTS: Final[dict[str, tuple[str, str]]] = {
    "EC": ("America/Guayaquil", "USD"),
    "AR": ("America/Argentina/Buenos_Aires", "ARS"),
    "BO": ("America/La_Paz", "BOB"),
    "BR": ("America/Sao_Paulo", "BRL"),
    "CL": ("America/Santiago", "CLP"),
    "CO": ("America/Bogota", "COP"),
    "CR": ("America/Costa_Rica", "CRC"),
    "DO": ("America/Santo_Domingo", "DOP"),
    "SV": ("America/El_Salvador", "USD"),
    "GT": ("America/Guatemala", "GTQ"),
    "HN": ("America/Tegucigalpa", "HNL"),
    "MX": ("America/Mexico_City", "MXN"),
    "NI": ("America/Managua", "NIO"),
    "PA": ("America/Panama", "USD"),
    "PY": ("America/Asuncion", "PYG"),
    "PE": ("America/Lima", "PEN"),
    "PR": ("America/Puerto_Rico", "USD"),
    "UY": ("America/Montevideo", "UYU"),
    "VE": ("America/Caracas", "VES"),
    "CA": ("America/Toronto", "CAD"),
    "US": ("America/New_York", "USD"),
    "ES": ("Europe/Madrid", "EUR"),
    "PT": ("Europe/Lisbon", "EUR"),
    "GB": ("Europe/London", "GBP"),
    "FR": ("Europe/Paris", "EUR"),
    "DE": ("Europe/Berlin", "EUR"),
    "IT": ("Europe/Rome", "EUR"),
    "NL": ("Europe/Amsterdam", "EUR"),
    "BE": ("Europe/Brussels", "EUR"),
    "CH": ("Europe/Zurich", "CHF"),
    "IE": ("Europe/Dublin", "EUR"),
    "AU": ("Australia/Sydney", "AUD"),
    "NZ": ("Pacific/Auckland", "NZD"),
    "JP": ("Asia/Tokyo", "JPY"),
    "KR": ("Asia/Seoul", "KRW"),
    "IN": ("Asia/Kolkata", "INR"),
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
