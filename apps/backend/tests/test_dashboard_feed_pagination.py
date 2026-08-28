from __future__ import annotations

from app.packages.engagement.services import dashboard_service


def test_home_feed_wraps_out_of_range_discover_page(monkeypatch) -> None:
    calls: list[int] = []

    def fake_get_tracks(_conn, *, page: int, limit: int, playable_only: bool):
        calls.append(page)
        assert limit == 24
        assert playable_only is False
        if page == 1:
            return ([{"id_track": 7, "nombre_track": "Signal"}], 26)
        return ([], 26)

    monkeypatch.setattr(dashboard_service, "get_tracks", fake_get_tracks)
    monkeypatch.setattr(dashboard_service, "get_genre_stats", lambda *_a, **_k: ([], 0))
    monkeypatch.setattr(dashboard_service, "get_artists", lambda *_a, **_k: ([], 0))
    monkeypatch.setattr(dashboard_service, "list_popular_catalog_playlists", lambda *_a, **_k: [])
    monkeypatch.setattr(dashboard_service, "get_summary", lambda *_a, **_k: {})
    monkeypatch.setattr(dashboard_service, "get_top_tracks_by_popularity", lambda *_a, **_k: [])
    monkeypatch.setattr(dashboard_service, "get_catalog_growth", lambda *_a, **_k: [])

    result = dashboard_service.get_home_feed(object(), discover_page=125)

    assert calls == [125, 1]
    assert result["discover"]["page"] == 1
    assert result["discover"]["total"] == 26
    assert result["discover"]["items"] == [
        {"id_track": 7, "nombre_track": "Signal"}
    ]
