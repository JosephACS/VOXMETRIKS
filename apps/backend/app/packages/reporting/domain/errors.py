"""Reporting domain errors — Spec 024."""

from __future__ import annotations


class ReportingError(Exception):
    def __init__(self, message: str, *, code: str = "reporting_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(ReportingError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, code="not_found")


class ValidationError(ReportingError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class StateError(ReportingError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_state")
