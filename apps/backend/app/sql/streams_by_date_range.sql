SELECT
    fecha,
    total_streams,
    unique_users,
    skip_count,
    avg_duration_ms
FROM agg_daily_streams
WHERE fecha BETWEEN ? AND ?
ORDER BY fecha ASC
