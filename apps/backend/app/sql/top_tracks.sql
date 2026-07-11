SELECT
    tp.id_track,
    tp.nombre_track,
    tp.nombre_artista,
    tp.nombre_genero,
    tp.popularity,
    tp.energy,
    tp.danceability,
    COALESCE(fs.total_streams, 0) AS total_streams
FROM agg_tracks_populares tp
LEFT JOIN (
    SELECT id_track, SUM(COALESCE(streams, 1)) AS total_streams
    FROM fact_streaming
    GROUP BY id_track
) fs ON fs.id_track = tp.id_track
ORDER BY total_streams DESC, tp.popularity DESC
LIMIT ?
