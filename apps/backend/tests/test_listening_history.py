"""Listening history — account-scoped app_listening_history."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture()
def hist_db(tmp_path):
    from app.core import schema_bootstrap

    schema_bootstrap._schema_ready = False
    db = tmp_path / "hist.duckdb"
    conn = duckdb.connect(str(db))
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.engagement.services.app_storage import ensure_app_tables
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )
    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_track (
            id_track INTEGER PRIMARY KEY, spotify_track_id VARCHAR,
            nombre_track VARCHAR NOT NULL, id_artista INTEGER, id_album INTEGER,
            id_genero INTEGER, explicit BOOLEAN DEFAULT FALSE,
            duration_ms INTEGER, popularity INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_artista (
            id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR
        )
        """
    )
    for tid in range(1, 6):
        conn.execute(
            "INSERT INTO dim_track (id_track, nombre_track, id_artista, duration_ms, popularity) VALUES (?, ?, 1, 180000, 50)",
            [tid, f"Track {tid}"],
        )
    conn.execute(
        "INSERT INTO dim_artista (id_artista, nombre_artista) VALUES (1, 'Artist')"
    )
    ensure_app_tables(conn)
    ensure_personal_subscription_tables(conn)
    now = utc_now()
    base = int(conn.execute("SELECT COALESCE(MAX(id), 0) FROM app_user").fetchone()[0])
    users = {}
    for i, name in enumerate(("owner", "member"), start=1):
        uid = base + i
        conn.execute(
            """
            INSERT INTO app_user
                (id, username, email, password_hash, role, plan, favorite_genre,
                 created_at, preferences_json, email_verified, auth_provider)
            VALUES (?, ?, ?, ?, 'user', 'Free', NULL, ?, '{}', TRUE, 'local')
            """,
            [uid, name, f"{name}@test.local", hash_password("pass"), now],
        )
        users[name] = uid
    yield conn, users
    conn.close()


def test_start_progress_complete_idempotent(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        complete_playback,
        list_history,
        start_playback,
        update_progress,
    )

    conn, users = hist_db
    uid = users["owner"]
    a = start_playback(conn, uid, 1, event_key="e1", source="player")
    b = start_playback(conn, uid, 1, event_key="e1", source="player")
    assert a["id"] == b["id"]
    update_progress(conn, uid, "e1", progress_ms=1000, listened_ms=1000)
    update_progress(conn, uid, "e1", progress_ms=500)  # monotonic
    # Explicit listened_ms required for completion threshold; progress is position only.
    complete_playback(conn, uid, "e1", progress_ms=180000, listened_ms=180000)
    page = list_history(conn, uid, page=1, limit=10)
    assert page["total"] == 1
    assert page["items"][0]["completed"] is True
    assert page["items"][0]["progress_ms"] >= 180000
    assert page["items"][0]["listened_ms"] >= 180000


def test_complete_does_not_infer_listened_from_progress(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        complete_playback,
        get_entry,
        meets_listen_threshold,
        start_playback,
        update_progress,
    )

    conn, users = hist_db
    uid = users["owner"]
    start_playback(conn, uid, 1, event_key="inf1")
    update_progress(conn, uid, "inf1", progress_ms=5000, listened_ms=5000)
    # Seek to end without listening that long — must not treat progress as listen time.
    out = complete_playback(conn, uid, "inf1", progress_ms=180000)
    assert out["listened_ms"] == 5000
    assert out["progress_ms"] >= 180000
    assert out["completed"] is False  # below 30s threshold
    assert meets_listen_threshold(5000, 180000) is False
    entry = get_entry(conn, uid, out["id"])
    assert entry["listened_ms"] == 5000


def test_short_track_threshold_uses_listened_ms(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        complete_playback,
        meets_listen_threshold,
        start_playback,
    )

    conn, users = hist_db
    uid = users["owner"]
    conn.execute("UPDATE dim_track SET duration_ms = 40000 WHERE id_track = 2")
    start_playback(conn, uid, 2, event_key="short1")
    # 50% of 40s = 20s
    assert meets_listen_threshold(20_000, 40_000) is True
    out = complete_playback(conn, uid, "short1", progress_ms=40000, listened_ms=20_000)
    assert out["completed"] is True
    assert out["listened_ms"] == 20_000


def test_isolation_and_delete(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        clear_history,
        delete_entry,
        list_history,
        start_playback,
    )
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
    )

    conn, users = hist_db
    ensure_free_subscription(conn, users["owner"])
    ensure_free_subscription(conn, users["member"])
    start_playback(conn, users["owner"], 1, event_key="o1")
    start_playback(conn, users["member"], 2, event_key="m1")
    owner = list_history(conn, users["owner"])
    member = list_history(conn, users["member"])
    assert owner["total"] == 1
    assert member["total"] == 1
    assert owner["items"][0]["id_track"] == 1
    assert member["items"][0]["id_track"] == 2
    eid = owner["items"][0]["id"]
    assert delete_entry(conn, users["member"], eid) is False
    assert delete_entry(conn, users["owner"], eid) is True
    assert clear_history(conn, users["member"]) == 1


def test_migrate_idempotent_and_bad_track(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        list_history,
        migrate_local_entries,
    )

    conn, users = hist_db
    uid = users["owner"]
    payload = [
        {"id_track": 1, "viewed_at": "2026-01-01T10:00:00"},
        {"id_track": 1, "viewed_at": "2026-01-01T10:00:00"},  # dup key
        {"id_track": 9999, "viewed_at": "2026-01-01T11:00:00"},  # missing
        {"id_track": 2, "viewed_at": "2026-01-02T10:00:00"},
    ]
    r1 = migrate_local_entries(conn, uid, payload)
    r2 = migrate_local_entries(conn, uid, payload)
    assert r1["imported"] == 2
    assert r1["invalid"] >= 1
    assert r2["imported"] == 0
    assert r2["skipped"] >= 2
    assert list_history(conn, uid)["total"] == 2


def test_track_not_found(hist_db):
    from app.packages.engagement.services.listening_history_service import start_playback

    conn, users = hist_db
    with pytest.raises(ValueError):
        start_playback(conn, users["owner"], 99999, event_key="x")


def test_pagination_order(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        list_history,
        start_playback,
    )

    conn, users = hist_db
    uid = users["owner"]
    for i, tid in enumerate((1, 2, 3), start=1):
        start_playback(conn, uid, tid, event_key=f"p{i}")
    page1 = list_history(conn, uid, page=1, limit=2)
    assert page1["total"] == 3
    assert len(page1["items"]) == 2
    assert page1["has_more"] is True
    assert page1["items"][0]["id_track"] == 3
    page2 = list_history(conn, uid, page=2, limit=2)
    assert len(page2["items"]) == 1
    assert page2["items"][0]["id_track"] == 1


def test_start_playback_concurrent_same_event_key(hist_db):
    """Serialized transactional start: same user/event_key → one row, same session."""
    import threading

    from app.packages.engagement.services.listening_history_service import (
        list_history,
        start_playback,
    )

    conn, users = hist_db
    uid = users["owner"]
    results: list[dict] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(4)

    def worker() -> None:
        try:
            barrier.wait(timeout=5)
            results.append(
                start_playback(conn, uid, 1, event_key="conc-same", source="player")
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(results) == 4
    ids = {r["id"] for r in results}
    assert len(ids) == 1
    page = list_history(conn, uid, page=1, limit=50)
    matching = [i for i in page["items"] if i.get("event_key") == "conc-same"]
    assert len(matching) == 1


def test_start_playback_concurrent_distinct_event_keys(hist_db):
    """Distinct event_keys under concurrency get distinct ids without constraint errors."""
    import threading

    from app.packages.engagement.services.listening_history_service import (
        list_history,
        start_playback,
    )

    conn, users = hist_db
    uid = users["owner"]
    results: list[dict] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(6)

    def worker(key: str, track_id: int) -> None:
        try:
            barrier.wait(timeout=5)
            results.append(
                start_playback(conn, uid, track_id, event_key=key, source="player")
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(f"conc-d{i}", (i % 5) + 1))
        for i in range(6)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(results) == 6
    ids = [r["id"] for r in results]
    assert len(ids) == len(set(ids))
    page = list_history(conn, uid, page=1, limit=50)
    keys = {i["event_key"] for i in page["items"] if str(i["event_key"]).startswith("conc-d")}
    assert keys == {f"conc-d{i}" for i in range(6)}


def test_start_playback_retry_metrics_monotonic(hist_db):
    from app.packages.engagement.services.listening_history_service import (
        get_entry,
        start_playback,
    )

    conn, users = hist_db
    uid = users["owner"]
    a = start_playback(
        conn, uid, 1, event_key="mono1", progress_ms=5_000, listened_ms=4_000
    )
    b = start_playback(
        conn, uid, 1, event_key="mono1", progress_ms=2_000, listened_ms=1_000
    )
    c = start_playback(
        conn, uid, 1, event_key="mono1", progress_ms=9_000, listened_ms=8_000
    )
    assert a["id"] == b["id"] == c["id"]
    entry = get_entry(conn, uid, a["id"])
    assert entry is not None
    assert entry["progress_ms"] == 9_000
    assert entry["listened_ms"] == 8_000
