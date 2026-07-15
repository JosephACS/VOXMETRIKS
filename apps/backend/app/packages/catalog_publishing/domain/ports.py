"""Media storage port — Spec 031.

Replaceable later by S3/MinIO; LocalMediaStorageProvider is the default.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional, Protocol


@dataclass(frozen=True)
class StoredMedia:
    stored_name: str
    relative_path: str
    absolute_path: Path
    byte_size: int
    sha256: str
    content_type: str
    duration_ms: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass(frozen=True)
class MediaValidationResult:
    passed: bool
    check_code: str
    detail: str = ""


class MediaStoragePort(Protocol):
    """Store private/published media under an org-scoped layout."""

    def store_private(
        self,
        *,
        organization_id: int,
        kind: str,
        filename: str,
        content_type: str,
        data: BinaryIO | bytes,
    ) -> StoredMedia:
        ...

    def promote_to_published(
        self,
        *,
        organization_id: int,
        relative_path: str,
    ) -> StoredMedia:
        ...

    def resolve_absolute(self, relative_path: str) -> Path:
        ...

    def validate_audio(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> list[MediaValidationResult]:
        ...

    def validate_image(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> list[MediaValidationResult]:
        ...
