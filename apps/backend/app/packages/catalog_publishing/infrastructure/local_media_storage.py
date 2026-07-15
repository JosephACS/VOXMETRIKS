"""Local filesystem media storage — Spec 031.

Layout:
  {MEDIA_STORAGE_ROOT}/private/{org_id}/...
  {MEDIA_STORAGE_ROOT}/published/{org_id}/...

UUID filenames, sha256 hashing, path-traversal prevention.
"""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Union

from app.core.config import get_settings
from app.packages.catalog_publishing.domain.errors import MediaValidationError
from app.packages.catalog_publishing.domain.ports import (
    MediaValidationResult,
    StoredMedia,
)

_AUDIO_EXT = {".wav", ".flac", ".mp3", ".m4a"}
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
_AUDIO_MIME = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/flac",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/aac",
}
_IMAGE_MIME = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# Magic-byte prefixes (partial — enough to reject obvious spoofs).
_MAGIC = (
    (b"RIFF", "wav"),
    (b"fLaC", "flac"),
    (b"ID3", "mp3"),
    (b"\xff\xfb", "mp3"),
    (b"\xff\xf3", "mp3"),
    (b"\xff\xf2", "mp3"),
    (b"\x00\x00\x00", "m4a"),  # ftyp often at offset 4
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"RIFF", "webp"),  # WEBP also starts RIFF....WEBP
)


def _read_bytes(data: Union[BinaryIO, bytes]) -> bytes:
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return data.read()


def _safe_filename(original: str) -> str:
    base = Path(original.replace("\\", "/")).name
    base = re.sub(r"[^\w.\-]+", "_", base)
    if not base or base in {".", ".."}:
        base = "upload.bin"
    return base[:180]


class LocalMediaStorageProvider:
    """Filesystem MediaStoragePort implementation."""

    def __init__(self, root: Optional[Path] = None) -> None:
        settings = get_settings()
        raw = root or Path(
            getattr(settings, "media_storage_root", None) or "data/media"
        )
        self.root = raw if raw.is_absolute() else (Path.cwd() / raw).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_audio_mb = float(
            getattr(settings, "media_max_audio_size_mb", 50) or 50
        )
        self.max_image_mb = float(
            getattr(settings, "media_max_image_size_mb", 10) or 10
        )
        self.min_cover_px = int(
            getattr(settings, "media_min_cover_px", 500) or 500
        )

    def _org_dir(self, zone: str, organization_id: int) -> Path:
        if zone not in ("private", "published"):
            raise MediaValidationError(f"Invalid zone: {zone}")
        path = (self.root / zone / str(int(organization_id))).resolve()
        if not str(path).startswith(str(self.root)):
            raise MediaValidationError("Path traversal blocked")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve_absolute(self, relative_path: str) -> Path:
        rel = relative_path.replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            raise MediaValidationError("Path traversal blocked")
        abs_path = (self.root / rel).resolve()
        if not str(abs_path).startswith(str(self.root)):
            raise MediaValidationError("Path traversal blocked")
        return abs_path

    def store_private(
        self,
        *,
        organization_id: int,
        kind: str,
        filename: str,
        content_type: str,
        data: Union[BinaryIO, bytes],
    ) -> StoredMedia:
        raw = _read_bytes(data)
        safe = _safe_filename(filename)
        ext = Path(safe).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest_dir = self._org_dir("private", organization_id)
        dest = dest_dir / stored_name
        dest.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        relative = f"private/{int(organization_id)}/{stored_name}"
        width = height = duration_ms = None
        if kind == "cover":
            width, height = _probe_image_dims(raw)
        elif kind == "audio" and ext == ".wav":
            duration_ms = _wav_duration_ms(raw)
        return StoredMedia(
            stored_name=stored_name,
            relative_path=relative,
            absolute_path=dest,
            byte_size=len(raw),
            sha256=digest,
            content_type=content_type,
            duration_ms=duration_ms,
            width=width,
            height=height,
        )

    def promote_to_published(
        self,
        *,
        organization_id: int,
        relative_path: str,
    ) -> StoredMedia:
        src = self.resolve_absolute(relative_path)
        if not src.is_file():
            raise MediaValidationError("Source media file missing")
        stored_name = src.name
        dest_dir = self._org_dir("published", organization_id)
        dest = dest_dir / stored_name
        if not dest.exists():
            shutil.copy2(src, dest)
        raw = dest.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        relative = f"published/{int(organization_id)}/{stored_name}"
        return StoredMedia(
            stored_name=stored_name,
            relative_path=relative,
            absolute_path=dest,
            byte_size=len(raw),
            sha256=digest,
            content_type="application/octet-stream",
        )

    def validate_audio(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> list[MediaValidationResult]:
        results: list[MediaValidationResult] = []
        ext = Path(_safe_filename(filename)).suffix.lower()
        max_bytes = int(self.max_audio_mb * 1024 * 1024)
        if len(data) > max_bytes:
            results.append(
                MediaValidationResult(
                    False,
                    "audio_size",
                    f"Audio exceeds {self.max_audio_mb} MB",
                )
            )
        else:
            results.append(MediaValidationResult(True, "audio_size", "ok"))

        if ext not in _AUDIO_EXT:
            results.append(
                MediaValidationResult(False, "audio_extension", f"Bad ext {ext}")
            )
        else:
            results.append(MediaValidationResult(True, "audio_extension", ext))

        ct = (content_type or "").split(";")[0].strip().lower()
        if ct and ct not in _AUDIO_MIME and not ct.startswith("audio/"):
            results.append(
                MediaValidationResult(False, "audio_mime", f"Bad mime {ct}")
            )
        else:
            results.append(MediaValidationResult(True, "audio_mime", ct or "n/a"))

        magic_ok = _looks_like_audio(data, ext)
        results.append(
            MediaValidationResult(
                magic_ok, "audio_magic", "ok" if magic_ok else "magic mismatch"
            )
        )
        return results

    def validate_image(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> list[MediaValidationResult]:
        results: list[MediaValidationResult] = []
        ext = Path(_safe_filename(filename)).suffix.lower()
        max_bytes = int(self.max_image_mb * 1024 * 1024)
        if len(data) > max_bytes:
            results.append(
                MediaValidationResult(
                    False,
                    "image_size",
                    f"Image exceeds {self.max_image_mb} MB",
                )
            )
        else:
            results.append(MediaValidationResult(True, "image_size", "ok"))

        if ext not in _IMAGE_EXT:
            results.append(
                MediaValidationResult(False, "image_extension", f"Bad ext {ext}")
            )
        else:
            results.append(MediaValidationResult(True, "image_extension", ext))

        ct = (content_type or "").split(";")[0].strip().lower()
        if ct and ct not in _IMAGE_MIME:
            results.append(
                MediaValidationResult(False, "image_mime", f"Bad mime {ct}")
            )
        else:
            results.append(MediaValidationResult(True, "image_mime", ct or "n/a"))

        magic_ok = _looks_like_image(data, ext)
        results.append(
            MediaValidationResult(
                magic_ok, "image_magic", "ok" if magic_ok else "magic mismatch"
            )
        )

        w, h = _probe_image_dims(data)
        if w is not None and h is not None:
            dim_ok = w >= self.min_cover_px and h >= self.min_cover_px
            results.append(
                MediaValidationResult(
                    dim_ok,
                    "image_dimensions",
                    f"{w}x{h} (min {self.min_cover_px})",
                )
            )
        else:
            # Soft: cannot parse dims for all formats — pass with detail
            results.append(
                MediaValidationResult(True, "image_dimensions", "unparsed")
            )
        return results


def _looks_like_audio(data: bytes, ext: str) -> bool:
    if len(data) < 12:
        return False
    if ext == ".wav" and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return True
    if ext == ".flac" and data[:4] == b"fLaC":
        return True
    if ext == ".mp3" and (
        data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
    ):
        return True
    if ext == ".m4a":
        # ISO BMFF: size(4) + 'ftyp'
        return len(data) >= 8 and data[4:8] == b"ftyp"
    # Unknown ext already failed; lenient magic
    return any(data.startswith(m[0]) for m in _MAGIC if m[1] != "jpg" and m[1] != "png")


def _looks_like_image(data: bytes, ext: str) -> bool:
    if len(data) < 8:
        return False
    if ext in {".jpg", ".jpeg"} and data[:3] == b"\xff\xd8\xff":
        return True
    if ext == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if ext == ".webp" and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    return False


def _probe_image_dims(data: bytes) -> tuple[Optional[int], Optional[int]]:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return int(w), int(h)
    if data[:3] == b"\xff\xd8\xff":
        # Minimal JPEG SOF scan
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                break
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return int(w), int(h)
            if marker == 0xD9:
                break
            length = struct.unpack(">H", data[i + 2 : i + 4])[0]
            i += 2 + length
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        if data[12:16] == b"VP8 " and len(data) >= 30:
            w = int.from_bytes(data[26:28], "little") & 0x3FFF
            h = int.from_bytes(data[28:30], "little") & 0x3FFF
            return w, h
    return None, None


def _wav_duration_ms(data: bytes) -> Optional[int]:
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return None
    try:
        channels = struct.unpack_from("<H", data, 22)[0]
        rate = struct.unpack_from("<I", data, 24)[0]
        bits = struct.unpack_from("<H", data, 34)[0]
        data_size = struct.unpack_from("<I", data, 40)[0]
        if channels <= 0 or rate <= 0 or bits <= 0:
            return None
        bytes_per_sec = channels * rate * (bits // 8)
        if bytes_per_sec <= 0:
            return None
        return int(data_size * 1000 / bytes_per_sec)
    except Exception:
        return None


def make_minimal_wav(duration_ms: int = 200, sample_rate: int = 8000) -> bytes:
    """Tiny valid mono 16-bit PCM WAV (no external deps) for demos/tests."""
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    pcm = b"\x00\x00" * n_samples
    data_size = len(pcm)
    hdr = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return hdr + pcm


def make_minimal_png(width: int = 512, height: int = 512) -> bytes:
    """Minimal valid solid PNG via zlib (stdlib only)."""
    import zlib

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b""
    row = b"\x00" + (b"\x40\x80\xc0" * width)
    for _ in range(height):
        raw += row
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
