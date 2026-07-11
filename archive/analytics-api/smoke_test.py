"""Smoke test for analytics-api services layer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.db import close_db, db_session, open_db
from app.services import (
    artist_service,
    audit_service,
    genre_service,
    recommendation_service,
    stream_service,
    user_service,
)

REQUIRED_KEYS = {"insight", "data", "metrics"}


def assert_shape(result: dict, name: str) -> None:
    missing = REQUIRED_KEYS - result.keys()
    if missing:
        raise AssertionError(f"{name} missing keys: {missing}")
    print(f"OK {name}: {result['insight'][:80]}...")


open_db()
with db_session() as conn:
    assert_shape(artist_service.get_artist_growth(conn), "get_artist_growth")
    assert_shape(artist_service.get_top_artists(conn, limit=5), "get_top_artists")
    assert_shape(artist_service.get_emerging_artists(conn), "get_emerging_artists")
    assert_shape(stream_service.get_daily_streams(conn, days=7), "get_daily_streams")
    assert_shape(stream_service.get_engagement_analysis(conn), "get_engagement_analysis")
    assert_shape(genre_service.get_genre_trends(conn, limit=5), "get_genre_trends")
    assert_shape(genre_service.get_genre_popularity(conn, limit=5), "get_genre_popularity")
    assert_shape(recommendation_service.get_top_recommendations(conn, limit=10), "get_top_recommendations")
    assert_shape(user_service.get_user_segments(conn), "get_user_segments")
    assert_shape(user_service.get_retention_analysis(conn), "get_retention_analysis")
    assert_shape(audit_service.get_pipeline_health(conn), "get_pipeline_health")
    assert_shape(audit_service.get_data_quality(conn), "get_data_quality")
close_db()
print("All service checks passed.")
