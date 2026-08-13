"""Conservative email-format check shared by identity and invitations."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]+$")
MAX_EMAIL_LEN = 254


def is_valid_email_format(email: str) -> bool:
    value = (email or "").strip()
    if not value or len(value) > MAX_EMAIL_LEN:
        return False
    return bool(_EMAIL_RE.fullmatch(value))
