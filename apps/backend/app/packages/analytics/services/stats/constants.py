"""Limits and table lists for stats / synthetic activity."""

MAX_TARGET_TOTAL = 2_000_000
MAX_CREATE_PER_RUN = 2_000_000
WARN_CREATE_ABOVE = 500_000
SYNTHETIC_BATCH_SIZE = 100_000

ACTIVITY_FACT_TABLES = [
    "fact_streaming",
    "fact_user_activity",
    "fact_playlist_activity",
    "fact_favorites",
    "fact_searches",
    "fact_stream_sessions",
]
