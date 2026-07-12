"""Platform ops domain errors — Spec 027."""


class PlatformOpsError(Exception):
    def __init__(self, message: str, *, code: str = "platform_ops_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(PlatformOpsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found")


class ValidationError(PlatformOpsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class StateError(PlatformOpsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="state_error")


class IdempotencyError(PlatformOpsError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="idempotency_conflict")
