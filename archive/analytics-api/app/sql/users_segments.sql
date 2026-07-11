SELECT
    segment,
    user_count,
    avg_plays,
    avg_session_min,
    retention_pct
FROM agg_user_engagement
ORDER BY user_count DESC
