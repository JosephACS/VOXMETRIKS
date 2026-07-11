SELECT
    id_genero,
    nombre_genero,
    popularidad_promedio,
    energia_promedio,
    total_tracks,
    total_artistas
FROM agg_genero_popularidad
ORDER BY popularidad_promedio DESC, total_tracks DESC
