SELECT
    id_artista,
    nombre_artista,
    streams_7d,
    streams_30d,
    growth_pct,
    total_followers
FROM agg_artist_growth
WHERE streams_7d > 0 OR streams_30d > 0
ORDER BY growth_pct DESC, streams_7d DESC
