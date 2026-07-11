SELECT
    id_genero,
    nombre_genero,
    streams_7d,
    streams_prev_7d,
    trend_pct,
    avg_popularity
FROM agg_genre_trends
ORDER BY trend_pct DESC, streams_7d DESC
