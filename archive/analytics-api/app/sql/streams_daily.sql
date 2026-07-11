SELECT
    fecha,
    total_streams,
    unique_users,
    unique_tracks,
    avg_duration_ms,
    skip_count
FROM agg_daily_streams
ORDER BY fecha DESC
