"""CS/Support domain errors — Spec 025."""

from __future__ import annotations


class CustomerSuccessError(Exception):
    def __init__(self, message: str, *, code: str = "customer_success_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(CustomerSuccessError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, code="not_found")


class ValidationError(CustomerSuccessError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class StateError(CustomerSuccessError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_state")
