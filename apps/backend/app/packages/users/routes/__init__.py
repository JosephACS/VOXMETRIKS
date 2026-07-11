"""COMPATIBILITY_ADAPTER — Spec 014 D2. Prefer ``app.packages.identity.routes``."""

from app.packages.identity.routes import users_router

__all__ = ["users_router"]
