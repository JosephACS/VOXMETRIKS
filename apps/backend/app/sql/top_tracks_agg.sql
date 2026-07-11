SELECT
    tp.id_track,
    tp.nombre_track,
    tp.nombre_artista,
    dg.nombre_genero,
    tp.popularity,
    dt.energy,
    dt.danceability,
    COALESCE(tp.total_streams, 0) AS total_streams
FROM agg_tracks_populares tp
LEFT JOIN dim_track dt ON dt.id_track = tp.id_track
LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
ORDER BY total_streams DESC, tp.popularity DESC
LIMIT ?
