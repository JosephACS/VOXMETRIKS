"""
VOXMETRIK_V2 — ELT Pipeline (Production Rewrite)
=================================================
Flow:
  Extract  → PocketBase CSV  OR  local Parquet (fallback)
  Load     → raw_spotify  (DuckDB staging table)
  Transform → dim_*, fact_*, agg_*  (warehouse tables)
  Control  → ctl_carga_dataset, ctl_auditoria

Fixes applied:
  [1] DuckDB Serialization: DB is deleted and recreated if corrupt/version-mismatch
  [2] PocketBase auth: uses /api/collections/_superusers/auth-with-password
      with fallback to /api/collections/users/auth-with-password
  [3] Null safety: COALESCE / NULLIF / TRIM throughout; pre-load DataFrame cleaning
  [4] No invented columns: all SQL uses only schema-defined columns
  [5] Python 3.12 compatible; no source-compiled dependencies

Run:
    python elt_pipeline.py
"""

# ── Load .env FIRST ───────────────────────────────────────────────────────────
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _env_candidate in [_HERE / ".env", _HERE.parent / ".env"]:
    if _env_candidate.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=str(_env_candidate), override=False)
        print(f"[ENV] Loaded: {_env_candidate}")
        break
else:
    print("[ENV] WARNING: No .env file found — relying on shell environment")

# ── Standard library ──────────────────────────────────────────────────────────
import io
import json
import logging
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ── Third-party — fail fast with clear messages ───────────────────────────────
try:
    import duckdb
except ImportError:
    sys.exit("ERROR: duckdb not installed.  Run: pip install duckdb==1.1.3")

try:
    import pandas as pd
except ImportError:
    sys.exit("ERROR: pandas not installed.  Run: pip install pandas==2.2.2 pyarrow==16.1.0")

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx not installed.  Run: pip install httpx==0.27.0")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("voxmetrik.pipeline")

# ── Configuration ─────────────────────────────────────────────────────────────
POCKETBASE_URL      = os.environ.get("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
POCKETBASE_EMAIL    = os.environ.get("POCKETBASE_EMAIL", "")
POCKETBASE_PASSWORD = os.environ.get("POCKETBASE_PASSWORD", "")
PB_COLLECTION       = os.environ.get("PB_COLLECTION", "datasets")
MAX_RETRIES         = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY_S       = int(os.environ.get("RETRY_DELAY_S", "2"))

_db_env = os.environ.get("DB_PATH", "").strip()
DB_PATH = Path(_db_env) if _db_env else _HERE / "duckdb" / "voxmetrik.duckdb"

PARQUET_PATH = _HERE / "data" / "processed" / "stage" / "raw_spotify.parquet"


# ═══════════════════════════════════════════════════════════════════════════════
#  DUCKDB CONNECTION — with corruption recovery
# ═══════════════════════════════════════════════════════════════════════════════

def _open_connection(db_path: Path, *, recreate: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Open a DuckDB connection.  If the file is corrupt or version-mismatched
    (SerializationError), back it up and recreate from scratch.

    Args:
        db_path:   Path to the .duckdb file.
        recreate:  Force deletion and recreation (used after first failure).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if recreate and db_path.exists():
        backup = db_path.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.duckdb")
        logger.warning(f"Moving corrupt DB to backup: {backup}")
        shutil.move(str(db_path), str(backup))
        # Also remove the WAL file if present
        wal = Path(str(db_path) + ".wal")
        if wal.exists():
            wal.unlink()

    try:
        conn = duckdb.connect(str(db_path), read_only=False)
        # Smoke-test the connection to surface serialization errors early
        conn.execute("SELECT 1").fetchone()
        logger.info(f"DuckDB connected: {db_path}")
        return conn
    except Exception as exc:
        err_str = str(exc).lower()
        if any(kw in err_str for kw in ("serial", "deserial", "incompatible", "version")):
            if not recreate:
                logger.warning(
                    f"DuckDB serialization/version error: {exc}\n"
                    "  → Recreating database from scratch…"
                )
                return _open_connection(db_path, recreate=True)
        raise RuntimeError(f"Cannot open DuckDB at {db_path}: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════════
#  SCHEMA — DDL
# ═══════════════════════════════════════════════════════════════════════════════

# Each statement uses CREATE TABLE IF NOT EXISTS so reruns are safe.
# Foreign-key constraints are advisory in DuckDB (not enforced) but kept for docs.
DDL_STATEMENTS: List[str] = [
    # ── Control tables ─────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS ctl_carga_dataset (
        id_carga         INTEGER PRIMARY KEY,
        fecha_carga      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        modo             VARCHAR   NOT NULL,
        registros_nuevos INTEGER   DEFAULT 0,
        total_raw        INTEGER   DEFAULT 0,
        estado           VARCHAR   NOT NULL DEFAULT 'PENDIENTE'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ctl_auditoria (
        id_auditoria   INTEGER PRIMARY KEY,
        accion         VARCHAR   NOT NULL,
        tabla_afectada VARCHAR,
        fecha_evento   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        detalles       VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ctl_reporte (
        id_reporte       INTEGER PRIMARY KEY,
        fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        tipo_reporte     VARCHAR,
        usuario          VARCHAR,
        detalles         VARCHAR
    )
    """,
    # ── Raw staging ────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS raw_spotify (
        id               INTEGER PRIMARY KEY,
        track_id         VARCHAR,
        track_name       VARCHAR,
        artists          VARCHAR,
        album_name       VARCHAR,
        popularity       INTEGER,
        duration_ms      INTEGER,
        explicit         BOOLEAN,
        danceability     DOUBLE,
        energy           DOUBLE,
        key_col          INTEGER,
        loudness         DOUBLE,
        mode_col         INTEGER,
        speechiness      DOUBLE,
        acousticness     DOUBLE,
        instrumentalness DOUBLE,
        liveness         DOUBLE,
        valence          DOUBLE,
        tempo            DOUBLE,
        time_signature   INTEGER,
        track_genre      VARCHAR,
        fecha_ingesta    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ── Dimensions ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS dim_artista (
        id_artista     INTEGER PRIMARY KEY,
        nombre_artista VARCHAR NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_genero (
        id_genero     INTEGER PRIMARY KEY,
        nombre_genero VARCHAR NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_album (
        id_album     INTEGER PRIMARY KEY,
        nombre_album VARCHAR NOT NULL,
        id_artista   INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_track (
        id_track         INTEGER PRIMARY KEY,
        spotify_track_id VARCHAR,
        nombre_track     VARCHAR NOT NULL,
        id_artista       INTEGER,
        id_album         INTEGER,
        id_genero        INTEGER,
        explicit         BOOLEAN,
        duration_ms      INTEGER
    )
    """,
    # ── Fact table ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS fact_audio_features (
        id_fact          INTEGER PRIMARY KEY,
        id_track         INTEGER,
        popularity       INTEGER,
        danceability     DOUBLE,
        energy           DOUBLE,
        loudness         DOUBLE,
        speechiness      DOUBLE,
        acousticness     DOUBLE,
        instrumentalness DOUBLE,
        liveness         DOUBLE,
        valence          DOUBLE,
        tempo            DOUBLE,
        key_col          INTEGER,
        mode_col         INTEGER,
        time_signature   INTEGER
    )
    """,
    # ── Aggregations ───────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS agg_top_artistas (
        id_artista           INTEGER PRIMARY KEY,
        nombre_artista       VARCHAR,
        promedio_popularidad DOUBLE,
        total_tracks         INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_genero_popularidad (
        id_genero            INTEGER PRIMARY KEY,
        nombre_genero        VARCHAR,
        popularidad_promedio DOUBLE,
        energia_promedio     DOUBLE,
        total_tracks         INTEGER,
        total_artistas       INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_distribucion_energia (
        rango_energia         VARCHAR PRIMARY KEY,
        cantidad_tracks       INTEGER,
        popularidad_promedio  DOUBLE,
        danceability_promedio DOUBLE
    )
    """,
]


def apply_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all tables (idempotent)."""
    for ddl in DDL_STATEMENTS:
        try:
            conn.execute(ddl)
        except Exception as exc:
            logger.error(f"DDL failed:\n{ddl.strip()}\nError: {exc}")
            raise
    logger.info("Schema applied ✓")


def get_real_columns(conn: duckdb.DuckDBPyConnection, table: str) -> List[str]:
    """Return the actual column names of a table from DuckDB metadata."""
    rows = conn.execute(f"DESCRIBE {table}").fetchall()
    return [row[0] for row in rows]


# ═══════════════════════════════════════════════════════════════════════════════
#  POCKETBASE CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class PocketBaseClient:
    """
    Minimal PocketBase HTTP client.
    - Tries superuser endpoint first (modern PocketBase ≥ 0.23)
    - Falls back to regular users collection
    - Retry + exponential back-off on transient errors
    """

    _ADMIN_ENDPOINT = "/api/collections/_superusers/auth-with-password"
    _USER_ENDPOINT  = "/api/collections/users/auth-with-password"

    def __init__(self, base_url: str, email: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.email    = email
        self.password = password
        self._token: Optional[str] = None

    # ── Auth ─────────────────────────────────────────────────────────────────

    def authenticate(self) -> bool:
        if not self.email or not self.password:
            logger.warning("PocketBase credentials not configured — skipping auth")
            return False

        # Try superuser endpoint first
        if self._try_auth(self._ADMIN_ENDPOINT, "superuser"):
            return True

        # Fallback to regular user
        logger.warning("Superuser auth failed or unavailable — trying user collection…")
        return self._try_auth(self._USER_ENDPOINT, "user")

    def _try_auth(self, endpoint: str, label: str) -> bool:
        url  = f"{self.base_url}{endpoint}"
        body = {"identity": self.email, "password": self.password}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"PocketBase {label} auth attempt {attempt}/{MAX_RETRIES} → {url}")
                resp = httpx.post(url, json=body, timeout=15)

                if resp.status_code == 200:
                    token = resp.json().get("token")
                    if token:
                        self._token = token
                        logger.info(f"PocketBase {label} auth ✓")
                        return True
                    logger.error("Auth response has no 'token' field")
                    return False

                if resp.status_code in (400, 401):
                    logger.error(
                        f"Auth rejected HTTP {resp.status_code}: {resp.text[:300]}\n"
                        f"  → Check POCKETBASE_EMAIL / POCKETBASE_PASSWORD in .env"
                    )
                    return False  # Wrong credentials — no point retrying

                if resp.status_code == 404:
                    logger.warning(f"Endpoint not found (404): {url}")
                    return False  # Endpoint missing — try next

                logger.warning(f"Unexpected HTTP {resp.status_code}: {resp.text[:200]}")

            except httpx.ConnectError:
                logger.warning(f"Cannot reach PocketBase at {self.base_url} (attempt {attempt})")
            except Exception as exc:
                logger.warning(f"Auth attempt {attempt} error: {exc}")

            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY_S * attempt
                logger.info(f"Retrying in {delay}s…")
                time.sleep(delay)

        logger.error(f"PocketBase {label} auth failed after {MAX_RETRIES} attempts")
        return False

    # ── API helpers ───────────────────────────────────────────────────────────

    @property
    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = self._token
        return h

    def get_records(
        self, collection: str, page: int = 1, per_page: int = 500
    ) -> Optional[Dict]:
        url    = f"{self.base_url}/api/collections/{collection}/records"
        params = {"page": page, "perPage": per_page, "sort": "-created"}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.get(url, headers=self._headers, params=params, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(
                    f"get_records({collection}) HTTP {resp.status_code}: {resp.text[:200]}"
                )
                return None
            except Exception as exc:
                logger.warning(f"get_records attempt {attempt} error: {exc}")
            time.sleep(RETRY_DELAY_S * attempt)
        return None

    def download_file(self, collection: str, record_id: str, filename: str) -> Optional[bytes]:
        url = f"{self.base_url}/api/files/{collection}/{record_id}/{filename}"
        try:
            resp = httpx.get(url, headers=self._headers, timeout=60, follow_redirects=True)
            if resp.status_code == 200:
                logger.info(f"Downloaded: {filename}  ({len(resp.content):,} bytes)")
                return resp.content
            logger.warning(f"File download HTTP {resp.status_code}: {url}")
        except Exception as exc:
            logger.error(f"File download error: {exc}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  EXTRACT
# ═══════════════════════════════════════════════════════════════════════════════

def extract_from_pocketbase(pb: PocketBaseClient) -> Optional[pd.DataFrame]:
    """Download the most-recent CSV record from PocketBase."""
    logger.info(f"Extracting from PocketBase collection '{PB_COLLECTION}'…")
    result = pb.get_records(PB_COLLECTION, per_page=1)
    if not result or not result.get("items"):
        logger.warning(f"No records in PocketBase collection '{PB_COLLECTION}'")
        return None

    record    = result["items"][0]
    record_id = record.get("id")
    logger.info(f"Found record id={record_id}")

    # Find any CSV file field in the record
    csv_field: Optional[str] = None
    for key, val in record.items():
        if isinstance(val, str) and val.lower().endswith(".csv"):
            csv_field = val
            break
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str) and item.lower().endswith(".csv"):
                    csv_field = item
                    break
        if csv_field:
            break

    if not csv_field:
        logger.warning("No CSV file found in record fields")
        return None

    raw_bytes = pb.download_file(PB_COLLECTION, record_id, csv_field)
    if not raw_bytes:
        return None

    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
        logger.info(f"PocketBase extract ✓  shape={df.shape}")
        return df
    except Exception as exc:
        logger.error(f"CSV parse error: {exc}")
        return None


def extract_from_parquet(path: Path) -> Optional[pd.DataFrame]:
    """Read the local Parquet fallback."""
    if not path.exists():
        logger.warning(f"Parquet not found at: {path}")
        return None
    try:
        df = pd.read_parquet(str(path))
        logger.info(f"Parquet extract ✓  shape={df.shape}  path={path}")
        return df
    except Exception as exc:
        logger.error(f"Parquet read error: {exc}")
        return None


def extract(pb: Optional[PocketBaseClient]) -> pd.DataFrame:
    """
    Extract with fallback chain:
      1. PocketBase (if credentials provided and server reachable)
      2. Local Parquet file
    Raises RuntimeError if both sources fail.
    """
    if pb is not None:
        df = extract_from_pocketbase(pb)
        if df is not None and not df.empty:
            return df

    df = extract_from_parquet(PARQUET_PATH)
    if df is not None and not df.empty:
        return df

    raise RuntimeError(
        "No data source available.\n"
        f"  • PocketBase: check credentials / server at {POCKETBASE_URL}\n"
        f"  • Parquet:    not found at {PARQUET_PATH}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD — normalize & insert into raw_spotify
# ═══════════════════════════════════════════════════════════════════════════════

# Map from possible source column names → canonical DuckDB column names
_COLUMN_MAP: Dict[str, str] = {
    # track id
    "track_id": "track_id",
    "id":        "track_id",      # only when no 'track_id' column exists
    # track name
    "track_name": "track_name",
    "name":       "track_name",
    # artists
    "artists":     "artists",
    "artist_name": "artists",
    "artist":      "artists",
    # album
    "album_name": "album_name",
    "album":      "album_name",
    # popularity
    "popularity": "popularity",
    # duration
    "duration_ms": "duration_ms",
    # explicit
    "explicit": "explicit",
    # audio features
    "danceability":     "danceability",
    "energy":           "energy",
    "key":              "key_col",
    "key_col":          "key_col",
    "loudness":         "loudness",
    "mode":             "mode_col",
    "mode_col":         "mode_col",
    "speechiness":      "speechiness",
    "acousticness":     "acousticness",
    "instrumentalness": "instrumentalness",
    "liveness":         "liveness",
    "valence":          "valence",
    "tempo":            "tempo",
    "time_signature":   "time_signature",
    # genre
    "track_genre": "track_genre",
    "genre":       "track_genre",
}

# Canonical defaults for each raw column (None = nullable, keep as-is)
_RAW_DEFAULTS: Dict[str, Any] = {
    "track_id":        None,
    "track_name":      None,
    "artists":         None,
    "album_name":      None,
    "popularity":      0,
    "duration_ms":     0,
    "explicit":        False,
    "danceability":    0.0,
    "energy":          0.0,
    "key_col":         0,
    "loudness":        0.0,
    "mode_col":        0,
    "speechiness":     0.0,
    "acousticness":    0.0,
    "instrumentalness":0.0,
    "liveness":        0.0,
    "valence":         0.0,
    "tempo":           0.0,
    "time_signature":  4,
    "track_genre":     None,
}

_FLOAT_COLS = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
]
_INT_COLS   = ["key_col", "mode_col", "time_signature", "popularity", "duration_ms"]


def _clean_string_col(series: pd.Series) -> pd.Series:
    """Strip whitespace; replace empty strings and 'nan'/'none' with NaN."""
    s = series.astype(str).str.strip()
    s = s.replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "None": pd.NA, "NaN": pd.NA})
    return s


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename, coerce types, fill defaults, deduplicate.
    Returns a clean DataFrame with row-numbered 'id' column prepended.
    """
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Build rename map (skip 'id' if 'track_id' also present)
    rename_map: Dict[str, str] = {}
    for col in df.columns:
        if col in _COLUMN_MAP:
            target = _COLUMN_MAP[col]
            # Don't let bare 'id' overwrite an existing 'track_id'
            if col == "id" and "track_id" in df.columns:
                continue
            rename_map[col] = target
    df.rename(columns=rename_map, inplace=True)

    # Deduplicate columns (keep first occurrence)
    df = df.loc[:, ~df.columns.duplicated()]

    # Add missing canonical columns with defaults
    for col, default in _RAW_DEFAULTS.items():
        if col not in df.columns:
            logger.warning(f"Column '{col}' missing in source — using default: {default!r}")
            df[col] = default

    # Clean string columns
    for col in ("track_id", "track_name", "artists", "album_name", "track_genre"):
        if col in df.columns:
            df[col] = _clean_string_col(df[col])

    # Coerce numeric types
    for col in _FLOAT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in _INT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("Int64").astype(int)

    # Coerce explicit to bool
    if df["explicit"].dtype == object:
        df["explicit"] = df["explicit"].map(
            lambda v: str(v).strip().lower() in ("true", "1", "yes")
        )
    df["explicit"] = df["explicit"].astype(bool)

    # Drop rows where track_name is null (NOT NULL in dim_track)
    before = len(df)
    df = df[df["track_name"].notna() & (df["track_name"].str.strip() != "")]
    dropped = before - len(df)
    if dropped:
        logger.warning(f"Dropped {dropped:,} rows with null/empty track_name")

    # Deduplicate on track_id (keep first occurrence)
    if df["track_id"].notna().any():
        df = df.drop_duplicates(subset=["track_id"], keep="first")

    df = df.reset_index(drop=True)
    # Insert sequential integer id (1-based) as primary key for raw_spotify
    df.insert(0, "id", range(1, len(df) + 1))

    logger.info(f"Normalized DataFrame: {len(df):,} rows, {len(df.columns)} columns")
    return df


def load_raw(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    """
    Replace raw_spotify content with the normalized DataFrame.
    Returns number of rows inserted.
    """
    df_norm = _normalize_df(df)

    # Only load columns that exist in the raw_spotify schema
    raw_schema_cols = list(_RAW_DEFAULTS.keys())
    available       = [c for c in raw_schema_cols if c in df_norm.columns]
    df_load         = df_norm[["id"] + available].copy()

    logger.info(f"Loading {len(df_load):,} rows into raw_spotify…")

    conn.execute("DELETE FROM raw_spotify")
    conn.register("_df_raw", df_load)
    cols_sql = ", ".join(available)
    conn.execute(f"""
        INSERT INTO raw_spotify (id, {cols_sql})
        SELECT id, {cols_sql} FROM _df_raw
    """)
    conn.unregister("_df_raw")

    count = conn.execute("SELECT COUNT(*) FROM raw_spotify").fetchone()[0]
    logger.info(f"raw_spotify loaded ✓  rows={count:,}")
    return count


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSFORM — dimensions, fact, aggregations
# ═══════════════════════════════════════════════════════════════════════════════

def transform(conn: duckdb.DuckDBPyConnection) -> None:
    """Run all transformation steps in dependency order."""
    logger.info("Starting transform phase…")
    _transform_dim_artista(conn)
    _transform_dim_genero(conn)
    _transform_dim_album(conn)
    _transform_dim_track(conn)
    _transform_fact_audio_features(conn)
    _transform_agg_top_artistas(conn)
    _transform_agg_genero_popularidad(conn)
    _transform_agg_distribucion_energia(conn)
    logger.info("Transform phase complete ✓")


def _transform_dim_artista(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM dim_artista")
    conn.execute("""
        INSERT INTO dim_artista (id_artista, nombre_artista)
        SELECT
            ROW_NUMBER() OVER (ORDER BY artists) AS id_artista,
            artists                              AS nombre_artista
        FROM (
            SELECT DISTINCT TRIM(COALESCE(artists, '')) AS artists
            FROM raw_spotify
            WHERE artists IS NOT NULL
              AND NULLIF(TRIM(artists), '') IS NOT NULL
        ) t
    """)
    n = conn.execute("SELECT COUNT(*) FROM dim_artista").fetchone()[0]
    logger.info(f"dim_artista    → {n:,} rows")


def _transform_dim_genero(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM dim_genero")
    conn.execute("""
        INSERT INTO dim_genero (id_genero, nombre_genero)
        SELECT
            ROW_NUMBER() OVER (ORDER BY track_genre) AS id_genero,
            track_genre                              AS nombre_genero
        FROM (
            SELECT DISTINCT TRIM(COALESCE(track_genre, '')) AS track_genre
            FROM raw_spotify
            WHERE track_genre IS NOT NULL
              AND NULLIF(TRIM(track_genre), '') IS NOT NULL
        ) t
    """)
    n = conn.execute("SELECT COUNT(*) FROM dim_genero").fetchone()[0]
    logger.info(f"dim_genero     → {n:,} rows")


def _transform_dim_album(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM dim_album")
    conn.execute("""
        INSERT INTO dim_album (id_album, nombre_album, id_artista)
        SELECT
            ROW_NUMBER() OVER (ORDER BY t.album_name, t.artists) AS id_album,
            t.album_name,
            da.id_artista
        FROM (
            SELECT DISTINCT
                TRIM(COALESCE(album_name, '')) AS album_name,
                TRIM(COALESCE(artists,    '')) AS artists
            FROM raw_spotify
            WHERE album_name IS NOT NULL
              AND NULLIF(TRIM(album_name), '') IS NOT NULL
        ) t
        LEFT JOIN dim_artista da ON da.nombre_artista = t.artists
    """)
    n = conn.execute("SELECT COUNT(*) FROM dim_album").fetchone()[0]
    logger.info(f"dim_album      → {n:,} rows")


def _transform_dim_track(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Build dim_track from raw_spotify.
    - COALESCE ensures nombre_track is never NULL (required NOT NULL)
    - LEFT JOINs are safe: missing artists/albums/genres produce NULLs, not errors
    - Deduplication on spotify_track_id keeps one row per track
    """
    conn.execute("DELETE FROM dim_track")
    conn.execute("""
        INSERT INTO dim_track (
            id_track, spotify_track_id, nombre_track,
            id_artista, id_album, id_genero, explicit, duration_ms
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY rs.id)          AS id_track,
            rs.track_id                                  AS spotify_track_id,
            COALESCE(NULLIF(TRIM(rs.track_name), ''), 'Unknown Track')
                                                         AS nombre_track,
            da.id_artista,
            dal.id_album,
            dg.id_genero,
            rs.explicit,
            rs.duration_ms
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY COALESCE(track_id, CAST(id AS VARCHAR))
                    ORDER BY id
                ) AS rn
            FROM raw_spotify
            WHERE track_name IS NOT NULL
              AND NULLIF(TRIM(track_name), '') IS NOT NULL
        ) rs
        LEFT JOIN dim_artista da  ON da.nombre_artista = TRIM(COALESCE(rs.artists,    ''))
        LEFT JOIN dim_album   dal ON dal.nombre_album  = TRIM(COALESCE(rs.album_name, ''))
                                 AND dal.id_artista    = da.id_artista
        LEFT JOIN dim_genero  dg  ON dg.nombre_genero  = TRIM(COALESCE(rs.track_genre, ''))
        WHERE rs.rn = 1
    """)
    n = conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
    logger.info(f"dim_track      → {n:,} rows")


def _transform_fact_audio_features(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Populate fact_audio_features from raw_spotify joined to dim_track.
    Join on spotify_track_id (preferred) with fallback on track name + raw id.
    """
    conn.execute("DELETE FROM fact_audio_features")
    conn.execute("""
        INSERT INTO fact_audio_features (
            id_fact, id_track,
            popularity, danceability, energy, loudness,
            speechiness, acousticness, instrumentalness,
            liveness, valence, tempo, key_col, mode_col, time_signature
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY rs.id)  AS id_fact,
            dt.id_track,
            COALESCE(rs.popularity,       0)    AS popularity,
            COALESCE(rs.danceability,     0.0)  AS danceability,
            COALESCE(rs.energy,           0.0)  AS energy,
            COALESCE(rs.loudness,         0.0)  AS loudness,
            COALESCE(rs.speechiness,      0.0)  AS speechiness,
            COALESCE(rs.acousticness,     0.0)  AS acousticness,
            COALESCE(rs.instrumentalness, 0.0)  AS instrumentalness,
            COALESCE(rs.liveness,         0.0)  AS liveness,
            COALESCE(rs.valence,          0.0)  AS valence,
            COALESCE(rs.tempo,            0.0)  AS tempo,
            COALESCE(rs.key_col,          0)    AS key_col,
            COALESCE(rs.mode_col,         0)    AS mode_col,
            COALESCE(rs.time_signature,   4)    AS time_signature
        FROM raw_spotify rs
        INNER JOIN dim_track dt
            ON dt.spotify_track_id = rs.track_id
            OR (
                dt.spotify_track_id IS NULL
                AND dt.nombre_track = TRIM(COALESCE(rs.track_name, ''))
            )
        WHERE rs.track_name IS NOT NULL
          AND NULLIF(TRIM(rs.track_name), '') IS NOT NULL
    """)
    n = conn.execute("SELECT COUNT(*) FROM fact_audio_features").fetchone()[0]
    logger.info(f"fact_audio_features → {n:,} rows")


def _transform_agg_top_artistas(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM agg_top_artistas")
    conn.execute("""
        INSERT INTO agg_top_artistas (
            id_artista, nombre_artista, promedio_popularidad, total_tracks
        )
        SELECT
            da.id_artista,
            da.nombre_artista,
            ROUND(AVG(CAST(COALESCE(faf.popularity, 0) AS DOUBLE)), 2) AS promedio_popularidad,
            COUNT(dt.id_track)                                          AS total_tracks
        FROM dim_artista da
        LEFT JOIN dim_track           dt  ON dt.id_artista = da.id_artista
        LEFT JOIN fact_audio_features faf ON faf.id_track  = dt.id_track
        GROUP BY da.id_artista, da.nombre_artista
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_top_artistas").fetchone()[0]
    logger.info(f"agg_top_artistas    → {n:,} rows")


def _transform_agg_genero_popularidad(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM agg_genero_popularidad")
    conn.execute("""
        INSERT INTO agg_genero_popularidad (
            id_genero, nombre_genero,
            popularidad_promedio, energia_promedio,
            total_tracks, total_artistas
        )
        SELECT
            dg.id_genero,
            dg.nombre_genero,
            ROUND(AVG(CAST(COALESCE(faf.popularity, 0) AS DOUBLE)), 2) AS popularidad_promedio,
            ROUND(AVG(CAST(COALESCE(faf.energy,     0) AS DOUBLE)), 3) AS energia_promedio,
            COUNT(dt.id_track)                                          AS total_tracks,
            COUNT(DISTINCT dt.id_artista)                               AS total_artistas
        FROM dim_genero dg
        LEFT JOIN dim_track           dt  ON dt.id_genero = dg.id_genero
        LEFT JOIN fact_audio_features faf ON faf.id_track = dt.id_track
        GROUP BY dg.id_genero, dg.nombre_genero
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_genero_popularidad").fetchone()[0]
    logger.info(f"agg_genero_popularidad → {n:,} rows")


def _transform_agg_distribucion_energia(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM agg_distribucion_energia")
    conn.execute("""
        INSERT INTO agg_distribucion_energia (
            rango_energia, cantidad_tracks,
            popularidad_promedio, danceability_promedio
        )
        SELECT
            CASE
                WHEN energy < 0.2 THEN '1_muy_baja'
                WHEN energy < 0.4 THEN '2_baja'
                WHEN energy < 0.6 THEN '3_media'
                WHEN energy < 0.8 THEN '4_alta'
                ELSE                    '5_muy_alta'
            END                                                        AS rango_energia,
            COUNT(*)                                                   AS cantidad_tracks,
            ROUND(AVG(CAST(COALESCE(popularity,   0) AS DOUBLE)), 2)  AS popularidad_promedio,
            ROUND(AVG(CAST(COALESCE(danceability, 0) AS DOUBLE)), 3)  AS danceability_promedio
        FROM fact_audio_features
        WHERE energy IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_distribucion_energia").fetchone()[0]
    logger.info(f"agg_distribucion_energia → {n:,} rows")


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTROL TABLE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _register_load(
    conn: duckdb.DuckDBPyConnection,
    modo: str,
    registros_nuevos: int,
    total_raw: int,
    estado: str,
) -> None:
    next_id = conn.execute(
        "SELECT COALESCE(MAX(id_carga), 0) + 1 FROM ctl_carga_dataset"
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO ctl_carga_dataset
            (id_carga, fecha_carga, modo, registros_nuevos, total_raw, estado)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        """,
        [next_id, modo, registros_nuevos, total_raw, estado],
    )


def _audit(
    conn: duckdb.DuckDBPyConnection, accion: str, tabla: str, detalles: str
) -> None:
    next_id = conn.execute(
        "SELECT COALESCE(MAX(id_auditoria), 0) + 1 FROM ctl_auditoria"
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO ctl_auditoria (id_auditoria, accion, tabla_afectada, detalles)
        VALUES (?, ?, ?, ?)
        """,
        [next_id, accion, tabla, detalles],
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline() -> None:
    start = datetime.now()
    logger.info("=" * 70)
    logger.info("  VOXMETRIK_V2 — ELT Pipeline")
    logger.info(f"  Started: {start:%Y-%m-%d %H:%M:%S}")
    logger.info(f"  DB_PATH: {DB_PATH}")
    logger.info("=" * 70)

    # 1 ── Open DuckDB (with corruption recovery) ────────────────────────────
    conn = _open_connection(DB_PATH)

    try:
        # 2 ── Apply schema ──────────────────────────────────────────────────
        apply_schema(conn)

        # 3 ── PocketBase auth ───────────────────────────────────────────────
        pb: Optional[PocketBaseClient] = None
        if POCKETBASE_EMAIL and POCKETBASE_PASSWORD:
            pb = PocketBaseClient(POCKETBASE_URL, POCKETBASE_EMAIL, POCKETBASE_PASSWORD)
            if not pb.authenticate():
                logger.warning("PocketBase unavailable — falling back to local parquet")
                pb = None
        else:
            logger.warning("PocketBase credentials not set — using local parquet only")

        # 4 ── Extract ───────────────────────────────────────────────────────
        logger.info("─── EXTRACT ───────────────────────────────────────────────")
        df = extract(pb)
        logger.info(f"Extracted {len(df):,} rows, {len(df.columns)} columns")

        # 5 ── Load raw ──────────────────────────────────────────────────────
        logger.info("─── LOAD ──────────────────────────────────────────────────")
        total_raw = load_raw(conn, df)

        # 6 ── Transform ─────────────────────────────────────────────────────
        logger.info("─── TRANSFORM ─────────────────────────────────────────────")
        transform(conn)

        # 7 ── Register success ──────────────────────────────────────────────
        _register_load(conn, "FULL", total_raw, total_raw, "EXITOSO")
        _audit(conn, "ELT_PIPELINE", "all", f"OK rows={total_raw}")
        conn.commit()

        elapsed = (datetime.now() - start).total_seconds()
        logger.info("=" * 70)
        logger.info(f"  Pipeline SUCCESS ✓   ({elapsed:.1f}s)")
        logger.info("=" * 70)

    except Exception as exc:
        logger.error(f"Pipeline FAILED: {exc}", exc_info=True)
        try:
            _register_load(conn, "FULL", 0, 0, "ERROR")
            _audit(conn, "ELT_ERROR", "pipeline", str(exc)[:500])
            conn.commit()
        except Exception:
            pass
        raise SystemExit(1)

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_pipeline()