"""
Bootstrap Bronze catalog when no PocketBase / parquet source exists.
Generates a realistic Spotify-style track dataset for demo ELT runs.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import List

import pandas as pd

GENRES = [
    "pop", "rock", "hip-hop", "latin", "electronic", "indie", "r-n-b",
    "metal", "jazz", "classical", "reggae", "country", "blues", "folk",
    "soul", "funk", "dance", "ambient", "punk", "k-pop",
]

FIRST = [
    "Midnight", "Golden", "Neon", "Silent", "Electric", "Crystal", "Velvet",
    "Urban", "Cosmic", "Frozen", "Wild", "Hidden", "Burning", "Endless",
    "Parallel", "Digital", "Scarlet", "Ocean", "Phantom", "Solar",
]
SECOND = [
    "Dreams", "Pulse", "Echo", "Horizon", "Velocity", "Mirage", "Paradox",
    "Frequency", "Shadow", "Gravity", "Spectrum", "Voyage", "Reverie",
    "Circuit", "Ember", "Cascade", "Nebula", "Rhythm", "Silhouette", "Aura",
]


def _unique_artist_names(n: int, rng: random.Random) -> List[str]:
    """Globally unique artist names — avoids repetitive prefix clusters (Blue *, DJ *, etc.)."""
    names: List[str] = []
    seen: set[str] = set()
    i = 0
    while len(names) < n:
        i += 1
        base = f"{rng.choice(FIRST)} {rng.choice(SECOND)}"
        name = f"{base} #{i:05d}"
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names


DEMO_TRACK_TITLES = [
    "Vámonos a Marte",
    "Despacito",
    "Bailando",
    "La Bicicleta",
    "Titi Me Preguntó",
    "Monaco",
    "Die for You",
    "Blinding Lights",
    "Shape of You",
    "Bad Guy",
    "Levitating",
    "Flowers",
    "As It Was",
    "Peaches",
    "Dákiti",
    "Ella Baila Sola",
    "Columbia",
    "Where She Goes",
    "TQG",
    "Shakira: Bzrp Music Sessions, Vol. 53",
]


def _track_name(i: int, rng: random.Random) -> str:
    if i < len(DEMO_TRACK_TITLES):
        return DEMO_TRACK_TITLES[i]
    return f"{rng.choice(FIRST)} {rng.choice(SECOND)} #{i + 1:05d}"


def _unique_album_name(i: int, rng: random.Random) -> str:
    """One distinct album title per source track row."""
    base = f"{rng.choice(FIRST)} {rng.choice(SECOND)}"
    return f"{base} #A{i:05d}"


def generate_bronze_dataframe(n_tracks: int = 8_500, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    n_artists = max(400, n_tracks // 18)
    artists = _unique_artist_names(n_artists, rng)
    rows = []

    for i in range(n_tracks):
        genre = rng.choice(GENRES)
        artist = rng.choice(artists)
        album = _unique_album_name(i + 1, rng)
        pop = int(rng.gauss(52, 22))
        pop = max(0, min(100, pop))
        energy = round(max(0.05, min(0.99, rng.gauss(0.55, 0.22))), 4)
        dance = round(max(0.05, min(0.99, energy * 0.7 + rng.uniform(-0.15, 0.15))), 4)
        valence = round(max(0.05, min(0.99, rng.uniform(0.15, 0.95))), 4)
        tempo = round(rng.uniform(72, 168), 2)
        dur = rng.randint(120_000, 320_000)

        rows.append({
            "track_id": f"boot_{i+1:06d}",
            "track_name": _track_name(i, rng),
            "artists": artist,
            "album_name": album,
            "popularity": pop,
            "duration_ms": dur,
            "explicit": rng.random() < 0.12,
            "danceability": dance,
            "energy": energy,
            "key_col": rng.randint(0, 11),
            "loudness": round(rng.uniform(-18, -4), 2),
            "mode_col": rng.randint(0, 1),
            "speechiness": round(rng.uniform(0.03, 0.45), 4),
            "acousticness": round(rng.uniform(0, 0.85), 4),
            "instrumentalness": round(max(0, rng.uniform(-0.05, 0.75)), 4),
            "liveness": round(rng.uniform(0.05, 0.35), 4),
            "valence": valence,
            "tempo": tempo,
            "time_signature": rng.choice([3, 4, 5]),
            "track_genre": genre,
        })

    return pd.DataFrame(rows)


def ensure_bronze_parquet(path: Path, n_tracks: int = 8_500) -> pd.DataFrame:
    """Create bronze parquet if missing; return DataFrame."""
    if path.exists():
        return pd.read_parquet(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_bronze_dataframe(n_tracks=n_tracks)
    df.to_parquet(str(path), index=False)
    return df
