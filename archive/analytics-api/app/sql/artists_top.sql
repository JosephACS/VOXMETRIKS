SELECT
    id_artista,
    nombre_artista,
    promedio_popularidad,
    total_tracks,
    total_streams
FROM agg_top_artistas
ORDER BY total_streams DESC, promedio_popularidad DESC
