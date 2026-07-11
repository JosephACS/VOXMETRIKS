#!/usr/bin/env python3
"""Auth check + upload spotify_dataset.csv to PocketBase datasets collection."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if not os.environ.get("POCKETBASE_EMAIL", "").strip():
    load_dotenv(ROOT / ".env.example", override=True)

URL = os.environ.get("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
if "pocketbase" in URL and "127.0.0.1" not in URL and "localhost" not in URL:
    URL = "http://127.0.0.1:8090"
EMAIL = os.environ.get("POCKETBASE_EMAIL", "")
PASSWORD = os.environ.get("POCKETBASE_PASSWORD", "")
COLLECTION = os.environ.get("PB_COLLECTION", "datasets")
RECORD_ID = "cc9arh0oe73ifc5"


def _csv_path() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    print("Uso: python scripts/upload_dataset_to_pocketbase.py <ruta/al/spotify_dataset.csv>")
    print("El CSV no se guarda en data/ — tras el upload vive en PocketBase (nube).")
    sys.exit(1)


def auth(client: httpx.Client) -> str | None:
    for endpoint, label in [
        ("/api/collections/_superusers/auth-with-password", "superuser"),
        ("/api/admins/auth-with-password", "admin (legacy)"),
        ("/api/collections/users/auth-with-password", "user"),
    ]:
        r = client.post(
            f"{URL}{endpoint}",
            json={"identity": EMAIL, "password": PASSWORD},
            timeout=15,
        )
        if r.status_code == 200:
            token = r.json().get("token")
            record = r.json().get("record", {})
            print(f"[auth] OK as {label}")
            print(f"[auth] id={record.get('id')} email={record.get('email', record.get('username', '?'))}")
            return token
        print(f"[auth] {label}: HTTP {r.status_code}")
    return None


def main() -> None:
    CSV = _csv_path()
    if not EMAIL or not PASSWORD:
        sys.exit("Missing POCKETBASE_EMAIL/PASSWORD in .env")

    with httpx.Client() as client:
        token = auth(client)
        if not token:
            sys.exit("Auth failed — verify credentials at http://127.0.0.1:8090/_/")
        headers = {"Authorization": token}

        r = client.get(
            f"{URL}/api/collections/{COLLECTION}/records",
            headers=headers,
            params={"perPage": 5, "sort": "-created"},
            timeout=15,
        )
        print(f"[datasets] list HTTP {r.status_code}")
        if r.status_code == 200:
            items = r.json().get("items", [])
            print(f"[datasets] records: {len(items)}")
            for item in items:
                print(f"  - id={item.get('id')} file={item.get('file')}")

        if not CSV.exists():
            sys.exit(f"CSV not found for upload: {CSV}")

        print(f"[upload] Sending {CSV.name} ({CSV.stat().st_size // 1024 // 1024} MB)...")
        with CSV.open("rb") as fh:
            up = client.patch(
                f"{URL}/api/collections/{COLLECTION}/records/{RECORD_ID}",
                headers=headers,
                files={"file": (CSV.name, fh, "text/csv")},
                timeout=120,
            )
        if up.status_code not in (200, 204):
            print(f"[upload] PATCH failed {up.status_code}: {up.text[:500]}")
            # try create new record
            with CSV.open("rb") as fh:
                up = client.post(
                    f"{URL}/api/collections/{COLLECTION}/records",
                    headers=headers,
                    files={"file": (CSV.name, fh, "text/csv")},
                    timeout=120,
                )
            print(f"[upload] POST HTTP {up.status_code}")
            if up.status_code != 200:
                sys.exit(up.text[:500])
            rec = up.json()
        else:
            rec = up.json() if up.content else {"id": RECORD_ID}

        rid = rec.get("id") or RECORD_ID
        fname = rec.get("file") if isinstance(rec.get("file"), str) else rec.get("file", [None])
        if isinstance(fname, list):
            fname = fname[0] if fname else "?"
        print(f"[upload] OK record={rid} file={fname}")

        dl = client.get(
            f"{URL}/api/files/{COLLECTION}/{rid}/{fname}",
            headers=headers,
            timeout=60,
        )
        print(f"[verify] download HTTP {dl.status_code} bytes={len(dl.content)}")


if __name__ == "__main__":
    main()
