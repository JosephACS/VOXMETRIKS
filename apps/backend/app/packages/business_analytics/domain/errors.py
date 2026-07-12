"""Business analytics domain errors — Spec 023."""

from __future__ import annotations


class BusinessAnalyticsError(Exception):
    pass


class NotFoundError(BusinessAnalyticsError):
    pass


class ValidationError(BusinessAnalyticsError):
    pass
