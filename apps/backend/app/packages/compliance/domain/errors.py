"""Compliance domain errors — Spec 026."""


class ComplianceError(Exception):
    """Base compliance error."""

    def __init__(self, message: str, *, code: str = "compliance_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(ComplianceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found")


class ValidationError(ComplianceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class StateError(ComplianceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="state_error")


class DeletionBlockedError(ComplianceError):
    def __init__(self, message: str, *, blockers: list[str] | None = None) -> None:
        super().__init__(message, code="deletion_blocked")
        self.blockers = blockers or []
