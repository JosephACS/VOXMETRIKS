
-- TABLE: agg_distribucion_energia
CREATE TABLE agg_distribucion_energia (
    rango_energia VARCHAR NOT NULL,
    cantidad_tracks INTEGER,
    popularidad_promedio DOUBLE,
    danceability_promedio DOUBLE
);

-- TABLE: agg_genero_popularidad
CREATE TABLE agg_genero_popularidad (
    id_genero INTEGER NOT NULL,
    nombre_genero VARCHAR,
    popularidad_promedio DOUBLE,
    energia_promedio DOUBLE,
    total_tracks INTEGER,
    total_artistas INTEGER
);

-- TABLE: agg_top_artistas
CREATE TABLE agg_top_artistas (
    id_artista INTEGER NOT NULL,
    nombre_artista VARCHAR,
    promedio_popularidad DOUBLE,
    total_tracks INTEGER
);

-- TABLE: ctl_auditoria
CREATE TABLE ctl_auditoria (
    id_auditoria INTEGER NOT NULL,
    accion VARCHAR NOT NULL,
    tabla_afectada VARCHAR,
    fecha_evento TIMESTAMP NOT NULL,
    detalles VARCHAR
);

-- TABLE: ctl_carga_dataset
CREATE TABLE ctl_carga_dataset (
    id_carga INTEGER NOT NULL,
    fecha_carga TIMESTAMP NOT NULL,
    modo VARCHAR NOT NULL,
    registros_nuevos INTEGER,
    total_raw INTEGER,
    estado VARCHAR NOT NULL
);

-- TABLE: ctl_reporte
CREATE TABLE ctl_reporte (
    id_reporte INTEGER NOT NULL,
    fecha_generacion TIMESTAMP NOT NULL,
    tipo_reporte VARCHAR,
    usuario VARCHAR,
    detalles VARCHAR
);

-- TABLE: dim_album
CREATE TABLE dim_album (
    id_album INTEGER NOT NULL,
    nombre_album VARCHAR NOT NULL,
    id_artista INTEGER
);

-- TABLE: dim_artista
CREATE TABLE dim_artista (
    id_artista INTEGER NOT NULL,
    nombre_artista VARCHAR NOT NULL
);

-- TABLE: dim_genero
CREATE TABLE dim_genero (
    id_genero INTEGER NOT NULL,
    nombre_genero VARCHAR NOT NULL
);

-- TABLE: dim_track
CREATE TABLE dim_track (
    id_track INTEGER NOT NULL,
    spotify_track_id VARCHAR,
    nombre_track VARCHAR NOT NULL,
    id_artista INTEGER,
    id_album INTEGER,
    id_genero INTEGER,
    explicit BOOLEAN,
    duration_ms INTEGER
);

-- TABLE: fact_audio_features
CREATE TABLE fact_audio_features (
    id_fact INTEGER NOT NULL,
    id_track INTEGER,
    popularity INTEGER,
    danceability DOUBLE,
    energy DOUBLE,
    loudness DOUBLE,
    speechiness DOUBLE,
    acousticness DOUBLE,
    instrumentalness DOUBLE,
    liveness DOUBLE,
    valence DOUBLE,
    tempo DOUBLE,
    key_col INTEGER,
    mode_col INTEGER,
    time_signature INTEGER
);

-- TABLE: raw_spotify
CREATE TABLE raw_spotify (
    id INTEGER NOT NULL,
    track_id VARCHAR,
    track_name VARCHAR,
    artists VARCHAR,
    album_name VARCHAR,
    popularity INTEGER,
    duration_ms INTEGER,
    explicit BOOLEAN,
    danceability DOUBLE,
    energy DOUBLE,
    key_col INTEGER,
    loudness DOUBLE,
    mode_col INTEGER,
    speechiness DOUBLE,
    acousticness DOUBLE,
    instrumentalness DOUBLE,
    liveness DOUBLE,
    valence DOUBLE,
    tempo DOUBLE,
    time_signature INTEGER,
    track_genre VARCHAR,
    fecha_ingesta TIMESTAMP
);
