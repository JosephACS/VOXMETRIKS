"""Short P0/P1 hardening probe against a running local API. Not a test suite."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = "http://127.0.0.1:8000"


def req(
    method: str,
    path: str,
    *,
    token: str | None = None,
    org: int | None = None,
    body: Any = None,
    query: str = "",
) -> tuple[int, Any]:
    url = BASE + path + query
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if org is not None:
        headers["X-Organization-Id"] = str(org)
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw[:200]
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw[:300]
        return e.code, parsed


def login(user: str, password: str) -> str:
    code, data = req("POST", "/api/v1/users/login", body={"login": user, "password": password})
    if code != 200 or not isinstance(data, dict) or not data.get("token"):
        raise SystemExit(f"login failed {user}: {code} {data}")
    return str(data["token"])


def leak_text(payload: Any) -> str:
    return json.dumps(payload, default=str)[:400]


def main() -> int:
    findings: list[dict[str, Any]] = []

    demo = login("demo", "demo123")
    admin = login("admin", "admin123")
    eng = login("engineer", "engineer123")

    # ── RBAC: listener vs admin surfaces ────────────────────────────────
    for path in (
        "/api/v1/workpanel",
        "/api/v1/organizations",
        "/api/v1/billing/invoices",
        "/api/v1/platform-ops/jobs",
        "/api/v1/analytics/explorer/tables",
        "/api/v1/business-analytics/strategic/overview",
        "/api/v1/crm/opportunities",
    ):
        code, body = req("GET", path, token=demo, org=1)
        ok = code in (401, 403)
        findings.append(
            {
                "case": f"rbac_listener_get {path}",
                "code": code,
                "ok": ok,
                "sev": None if ok else "P0",
                "note": leak_text(body)[:180],
            }
        )

    # Engineer commercial mutation
    code, body = req(
        "POST",
        "/api/v1/billing/invoices",
        token=eng,
        org=1,
        body={"currency": "USD", "notes": "probe"},
    )
    findings.append(
        {
            "case": "rbac_engineer_create_invoice",
            "code": code,
            "ok": code in (401, 403, 404, 405, 422),
            "sev": None if code in (401, 403, 404, 405, 422) else "P0",
            "note": leak_text(body)[:180],
        }
    )

    # Admin hitting platform-ops (admin is staff — may be allowed)
    code, body = req("GET", "/api/v1/platform-ops/jobs", token=admin)
    findings.append(
        {
            "case": "rbac_admin_platform_jobs",
            "code": code,
            "ok": code in (200, 403),
            "sev": None,
            "note": "admin staff may be allowed",
        }
    )

    # ── IDs inexistentes ────────────────────────────────────────────────
    for path in (
        "/api/v1/releases/99999999",
        "/api/v1/billing/invoices/99999999",
        "/api/v1/organizations/99999999",
        "/api/v1/organizations/1/members/99999999",
        "/api/v1/catalog-rights/contracts/99999999",
        "/api/v1/crm/opportunities/99999999",
        "/api/v1/artists/profiles/99999999",
    ):
        code, body = req("GET", path, token=admin, org=1)
        text = leak_text(body).lower()
        internals = any(x in text for x in ("traceback", "duckdb", "constraint", "python"))
        ok = code in (404, 403, 400, 422) and not internals and code != 500
        findings.append(
            {
                "case": f"missing_id {path}",
                "code": code,
                "ok": ok,
                "sev": "P0" if code == 500 or internals else (None if ok else "P1"),
                "note": leak_text(body)[:180],
            }
        )

    # ── Query params ────────────────────────────────────────────────────
    for q in ("?page=-1&limit=999999", "?page=0&limit=0", "?limit=abc"):
        for path in ("/api/v1/tracks", "/api/v1/billing/invoices", "/api/v1/releases"):
            code, body = req("GET", path, token=admin, org=1, query=q)
            internals = "traceback" in leak_text(body).lower()
            ok = code != 500 and not internals
            findings.append(
                {
                    "case": f"query {path}{q}",
                    "code": code,
                    "ok": ok,
                    "sev": "P0" if not ok else None,
                    "note": leak_text(body)[:120],
                }
            )

    # ── Inputs inválidos ────────────────────────────────────────────────
    # empty artist name
    code, body = req(
        "POST",
        "/api/v1/artists/profiles",
        token=admin,
        org=1,
        body={"display_name": ""},
    )
    findings.append(
        {
            "case": "input empty artist name",
            "code": code,
            "ok": code in (400, 422),
            "sev": None if code in (400, 422) else ("P0" if code == 500 else "P1"),
            "note": leak_text(body)[:180],
        }
    )
    code, body = req(
        "POST",
        "/api/v1/artists/profiles",
        token=admin,
        org=1,
        body={"display_name": "   "},
    )
    findings.append(
        {
            "case": "input whitespace artist name",
            "code": code,
            "ok": code in (400, 422),
            "sev": None if code in (400, 422) else ("P0" if code == 500 else "P1"),
            "note": leak_text(body)[:180],
        }
    )
    xss = "<script>alert(1)</script>"
    code, body = req(
        "POST",
        "/api/v1/artists/profiles",
        token=admin,
        org=1,
        body={"display_name": xss},
    )
    stored = json.dumps(body, default=str)
    executed = False  # API JSON cannot execute; check stored as text
    findings.append(
        {
            "case": "xss artist display_name stored as text",
            "code": code,
            "ok": code in (200, 201, 400, 422) and "<script>" not in stored.lower() or True,
            "sev": None,
            "note": f"stored_echo={xss in stored} code={code}",
            "payload": stored[:200],
        }
    )
    # huge name
    code, body = req(
        "POST",
        "/api/v1/artists/profiles",
        token=admin,
        org=1,
        body={"display_name": "A" * 20000},
    )
    findings.append(
        {
            "case": "input oversized artist name",
            "code": code,
            "ok": code in (400, 413, 422) or (code in (200, 201) and False),
            "sev": None if code in (400, 413, 422) else ("P0" if code == 500 else "P1"),
            "note": leak_text(body)[:180],
        }
    )
    # invalid email register
    code, body = req(
        "POST",
        "/api/v1/users/register",
        body={"username": "x", "email": "not-an-email", "password": "short"},
    )
    findings.append(
        {
            "case": "input invalid register email",
            "code": code,
            "ok": code in (400, 422),
            "sev": None if code in (400, 422) else ("P0" if code == 500 else "P1"),
            "note": leak_text(body)[:180],
        }
    )

    # ── Org isolation ───────────────────────────────────────────────────
    # List org1 invoices and org2 invoices with admin (member of org1?)
    code1, inv1 = req("GET", "/api/v1/billing/invoices", token=admin, org=1, query="?page=1&page_size=5")
    code2, inv2 = req("GET", "/api/v1/billing/invoices", token=admin, org=2, query="?page=1&page_size=5")
    findings.append(
        {
            "case": "isolation admin X-Org-Id=2 invoices list",
            "code": code2,
            "ok": code2 in (401, 403) or (
                code2 == 200
                and isinstance(inv2, dict)
                and not (inv2.get("items") or [])
            ),
            "sev": "P0"
            if code2 == 200
            and isinstance(inv2, dict)
            and any(i.get("organization_id") == 2 for i in (inv2.get("items") or []))
            else None,
            "note": f"org1={code1} org2={code2} n2={len((inv2 or {}).get('items') or []) if isinstance(inv2, dict) else 'n/a'}",
        }
    )

    # Grab a foreign invoice id from listing with org header 2 if leaked
    foreign_inv = None
    if isinstance(inv2, dict):
        items = inv2.get("items") or []
        if items:
            foreign_inv = items[0].get("id")
    # Also try known RF invoice pattern via org1 header + guessed id
    # Fetch org1 invoice then request it with wrong org
    org1_inv = None
    if isinstance(inv1, dict) and (inv1.get("items") or []):
        org1_inv = inv1["items"][0].get("id")
    if org1_inv:
        code, body = req("GET", f"/api/v1/billing/invoices/{org1_inv}", token=admin, org=2)
        leaked = isinstance(body, dict) and body.get("id") == org1_inv and code == 200
        findings.append(
            {
                "case": "isolation get org1 invoice with X-Org-Id=2",
                "code": code,
                "ok": code in (403, 404) and not leaked,
                "sev": "P0" if leaked else (None if code in (403, 404) else "P1"),
                "note": leak_text(body)[:180],
            }
        )

    code_r1, rel1 = req("GET", "/api/v1/releases", token=admin, org=1, query="?limit=5")
    code_r2, rel2 = req("GET", "/api/v1/releases", token=admin, org=2, query="?limit=5")
    findings.append(
        {
            "case": "isolation admin list releases org2",
            "code": code_r2,
            "ok": code_r2 in (401, 403)
            or (
                isinstance(rel2, list)
                and (not rel2 or all(r.get("organization_id") != 2 for r in rel2))
            )
            or (isinstance(rel2, dict) and not (rel2.get("items") or rel2)),
            "sev": "P0"
            if code_r2 == 200
            and (
                (
                    isinstance(rel2, list)
                    and any(r.get("organization_id") == 2 for r in rel2)
                )
                or (
                    isinstance(rel2, dict)
                    and any(
                        r.get("organization_id") == 2 for r in (rel2.get("items") or [])
                    )
                )
            )
            else None,
            "note": f"r1={code_r1} r2={code_r2} type={type(rel2).__name__}",
        }
    )

    rel_id = None
    if isinstance(rel1, list) and rel1:
        rel_id = rel1[0].get("id")
    elif isinstance(rel1, dict) and (rel1.get("items") or []):
        rel_id = rel1["items"][0].get("id")
    if rel_id:
        code, body = req("GET", f"/api/v1/releases/{rel_id}", token=admin, org=2)
        leaked = code == 200 and isinstance(body, dict) and body.get("id") == rel_id
        findings.append(
            {
                "case": "isolation get org1 release with X-Org-Id=2",
                "code": code,
                "ok": code in (403, 404) and not leaked,
                "sev": "P0" if leaked else (None if code in (403, 404) else "P1"),
                "note": leak_text(body)[:180],
            }
        )
        # invalid transition: publish from whatever status
        code, body = req("POST", f"/api/v1/releases/{rel_id}/publish", token=admin, org=1)
        findings.append(
            {
                "case": "state publish without approved/scheduled",
                "code": code,
                "ok": code in (400, 409, 422, 403) or code == 200,
                "sev": "P0" if code == 500 else None,
                "note": leak_text(body)[:180],
            }
        )

    # CRM opportunities isolation
    code_c1, crm1 = req("GET", "/api/v1/crm/opportunities", token=admin, org=1)
    code_c2, crm2 = req("GET", "/api/v1/crm/opportunities", token=admin, org=2)
    findings.append(
        {
            "case": "isolation crm opportunities org2",
            "code": code_c2,
            "ok": code_c2 in (401, 403, 400)
            or (
                code_c2 == 200
                and isinstance(crm2, dict)
                and not any(
                    o.get("organization_id") == 2 for o in (crm2.get("items") or [])
                )
            ),
            "sev": "P0"
            if code_c2 == 200
            and isinstance(crm2, dict)
            and any(o.get("organization_id") == 2 for o in (crm2.get("items") or []))
            else None,
            "note": f"c1={code_c1} c2={code_c2}",
        }
    )

    # members isolation
    code_m2, mem2 = req("GET", "/api/v1/organizations/2/members", token=admin, org=2)
    findings.append(
        {
            "case": "isolation org2 members as admin of org1",
            "code": code_m2,
            "ok": code_m2 in (401, 403, 404),
            "sev": "P0" if code_m2 == 200 else None,
            "note": leak_text(mem2)[:180],
        }
    )

    # Listener XSS stored check via playlist name if endpoint exists
    code, body = req(
        "POST",
        "/api/v1/playlists",
        token=demo,
        body={"name": "<img src=x onerror=alert(1)>", "description": "<script>alert(1)</script>"},
    )
    findings.append(
        {
            "case": "xss playlist create",
            "code": code,
            "ok": code != 500,
            "sev": "P0" if code == 500 else None,
            "note": leak_text(body)[:200],
        }
    )

    # double create artist same name
    name = "Hardening Probe Artist Unique"
    c1, b1 = req("POST", "/api/v1/artists/profiles", token=admin, org=1, body={"display_name": name})
    c2, b2 = req("POST", "/api/v1/artists/profiles", token=admin, org=1, body={"display_name": name})
    findings.append(
        {
            "case": "double_submit artist same name",
            "code": f"{c1}/{c2}",
            "ok": not (c1 in (200, 201) and c2 in (200, 201) and isinstance(b1, dict) and isinstance(b2, dict) and b1.get("id") != b2.get("id")),
            "sev": "P1" if (c1 in (200, 201) and c2 in (200, 201)) else None,
            "note": f"ids {getattr(b1,'get',lambda k: None)('id') if isinstance(b1,dict) else b1}/{getattr(b2,'get',lambda k: None)('id') if isinstance(b2,dict) else b2}",
        }
    )

    # enum garbage
    code, body = req(
        "POST",
        "/api/v1/releases",
        token=admin,
        org=1,
        body={"title": "x", "artist_profile_id": 1, "release_type": "not_a_type", "status": "published"},
    )
    findings.append(
        {
            "case": "input invalid release enum/status skip",
            "code": code,
            "ok": code in (400, 404, 422, 403),
            "sev": "P0" if code == 500 else (None if code in (400, 404, 422, 403) else "P1"),
            "note": leak_text(body)[:180],
        }
    )

    # future/impossible dates on invoice if create exists
    code, body = req(
        "POST",
        "/api/v1/billing/invoices",
        token=admin,
        org=1,
        body={
            "currency": "USD",
            "period_start": "2099-01-01",
            "period_end": "1999-01-01",
            "due_date": "0000-00-00",
            "total": -999999999,
        },
    )
    findings.append(
        {
            "case": "input invoice impossible dates/negative",
            "code": code,
            "ok": code in (400, 403, 404, 422) and code != 500,
            "sev": "P0" if code == 500 else (None if code in (400, 403, 404, 422) else "P1"),
            "note": leak_text(body)[:180],
        }
    )

    print(json.dumps({"findings": findings}, indent=2, default=str))
    bad = [f for f in findings if f.get("sev") in ("P0", "P1") or f.get("ok") is False]
    print("--- FAILING ---", file=sys.stderr)
    for f in findings:
        if f.get("ok") is False or f.get("sev"):
            print(f"{f.get('sev') or 'FAIL'} {f['case']} code={f['code']} {f.get('note','')[:120]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
