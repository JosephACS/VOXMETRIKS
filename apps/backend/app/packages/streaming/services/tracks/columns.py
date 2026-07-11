"""Track column lists for dim_track queries."""

TRACK_COLS = [
    "id_track", "spotify_track_id", "nombre_track",
    "id_artista", "id_album", "id_genero", "explicit", "duration_ms",
    "danceability", "energy", "loudness", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence", "tempo", "popularity",
]

TRACK_COLS_BASIC = [
    "id_track", "spotify_track_id", "nombre_track",
    "id_artista", "id_album", "id_genero", "explicit", "duration_ms",
]

TRACK_LIST_COLS = TRACK_COLS_BASIC + ["popularity", "nombre_artista", "nombre_genero"]

FEATURE_COLS = [
    "id_track", "popularity", "danceability", "energy", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
]

DETAIL_COLS = [
    "id_track", "spotify_track_id", "nombre_track",
    "id_artista", "id_album", "id_genero",
    "explicit", "duration_ms",
    "popularity", "danceability", "energy", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
    "nombre_artista", "nombre_genero",
]
