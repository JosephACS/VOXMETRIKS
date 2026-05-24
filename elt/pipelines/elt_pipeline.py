"""
VOXMETRIK_V2 — ELT Pipeline (Medallion Architecture Rewrite)
=============================================================
Architecture:
  Bronze  → Raw Parquet from PocketBase / local file
  Silver  → Cleaned, normalized, deduplicated Parquet
  Gold    → Dimensional model (dim_*, fact_*) + aggregations in DuckDB

Output:
  data/warehouse/voxmetrik.duckdb  ← single authoritative DW file

Tables created in DuckDB:
  Dimensions : dim_usuario, dim_artista, dim_genero, dim_album,
               dim_track, dim_playlist, dim_tiempo
  Facts      : fact_streaming
  Analytics  : agg_top_artistas, agg_genero_popularidad,
               agg_distribucion_energia
  Control    : ctl_carga_dataset, ctl_auditoria
  Staging    : raw_spotify (Bronze mirror)

Run:
    python elt/pipelines/elt_pipeline.py
"""

# ── Bootstrap: load .env from project root or pipeline dir ───────────────────
import os
import sys
from pathlib import Path

# Resolve project root (two levels up from elt/pipelines/)
_HERE        = Path(__file__).resolve().parent          # elt/pipelines/
_PROJECT_ROOT = _HERE.parent.parent                     # VOXMETRIK_V2/

for _env_candidate in [
    _PROJECT_ROOT / ".env",
    _HERE.parent / ".env",
    _HERE / ".env",
]:
    if _env_candidate.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=str(_env_candidate), override=False)
            print(f"[ENV] Loaded: {_env_candidate}")
        except ImportError:
            pass  # dotenv optional
        break
else:
    print("[ENV] WARNING: No .env found — relying on shell environment")

# ── Standard library ──────────────────────────────────────────────────────────
import io
import json
import logging
import shutil
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional

# ── Third-party — explicit fail messages ─────────────────────────────────────
try:
    import duckdb
except ImportError:
    sys.exit("ERROR: duckdb not installed.  Run: pip install duckdb")

try:
    import pandas as pd
except ImportError:
    sys.exit("ERROR: pandas not installed.  Run: pip install pandas pyarrow")

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx not installed.  Run: pip install httpx")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("voxmetrik.pipeline")

# ─────────────────────────────────────────────────────────────────────────────
#  PATH CONFIGURATION
#  All paths relative to project root so the pipeline works regardless of
#  the working directory the user invokes it from.
# ─────────────────────────────────────────────────────────────────────────────

# Allow override via DB_PATH env var; otherwise always land in data/warehouse/
_db_env = os.environ.get("DB_PATH", "").strip()
if _db_env:
    DB_PATH = Path(_db_env)
else:
    DB_PATH = _PROJECT_ROOT / "data" / "warehouse" / "voxmetrik.duckdb"

# Medallion layer directories
BRONZE_DIR = _PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = _PROJECT_ROOT / "data" / "silver"
GOLD_DIR   = _PROJECT_ROOT / "data" / "gold"

# Source parquet (Bronze input)
BRONZE_PARQUET = BRONZE_DIR / "raw_spotify.parquet"

# Silver output (cleaned parquet)
SILVER_PARQUET = SILVER_DIR / "silver_spotify.parquet"

# PocketBase config
POCKETBASE_URL      = os.environ.get("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
POCKETBASE_EMAIL    = os.environ.get("POCKETBASE_EMAIL", "")
POCKETBASE_PASSWORD = os.environ.get("POCKETBASE_PASSWORD", "")
PB_COLLECTION       = os.environ.get("PB_COLLECTION", "datasets")
MAX_RETRIES         = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY_S       = int(os.environ.get("RETRY_DELAY_S", "2"))


# ═══════════════════════════════════════════════════════════════════════════════
#  BRONZE LAYER — Raw extraction
#  Goal: get raw data and persist it as-is to data/bronze/raw_spotify.parquet
# ═══════════════════════════════════════════════════════════════════════════════

class PocketBaseClient:
    """Minimal PocketBase HTTP client with superuser + user fallback."""

    _ADMIN_ENDPOINT = "/api/collections/_superusers/auth-with-password"
    _USER_ENDPOINT  = "/api/collections/users/auth-with-password"

    def __init__(self, base_url: str, email: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.email    = email
        self.password = password
        self._token: Optional[str] = None

    def authenticate(self) -> bool:
        if not self.email or not self.password:
            logger.warning("PocketBase credentials not configured")
            return False
        if self._try_auth(self._ADMIN_ENDPOINT, "superuser"):
            return True
        logger.warning("Superuser auth failed — trying user collection…")
        return self._try_auth(self._USER_ENDPOINT, "user")

    def _try_auth(self, endpoint: str, label: str) -> bool:
        url  = f"{self.base_url}{endpoint}"
        body = {"identity": self.email, "password": self.password}
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.post(url, json=body, timeout=15)
                if resp.status_code == 200:
                    token = resp.json().get("token")
                    if token:
                        self._token = token
                        logger.info(f"PocketBase {label} auth ✓")
                        return True
                    return False
                if resp.status_code in (400, 401, 404):
                    return False
            except httpx.ConnectError:
                logger.warning(f"Cannot reach PocketBase at {self.base_url}")
            except Exception as exc:
                logger.warning(f"Auth error: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S * attempt)
        return False

    @property
    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = self._token
        return h

    def get_records(self, collection: str, page: int = 1, per_page: int = 500) -> Optional[Dict]:
        url    = f"{self.base_url}/api/collections/{collection}/records"
        params = {"page": page, "perPage": per_page, "sort": "-created"}
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = httpx.get(url, headers=self._headers, params=params, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
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
                return resp.content
        except Exception as exc:
            logger.error(f"File download error: {exc}")
        return None


def _bronze_from_pocketbase(pb: PocketBaseClient) -> Optional[pd.DataFrame]:
    """Pull latest CSV from PocketBase → DataFrame (raw, no cleaning)."""
    result = pb.get_records(PB_COLLECTION, per_page=1)
    if not result or not result.get("items"):
        logger.warning(f"No records in PocketBase '{PB_COLLECTION}'")
        return None

    record    = result["items"][0]
    record_id = record.get("id")
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
        logger.warning("No CSV field in PocketBase record")
        return None

    raw_bytes = pb.download_file(PB_COLLECTION, record_id, csv_field)
    if not raw_bytes:
        return None

    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
        logger.info(f"[BRONZE] PocketBase extract ✓  shape={df.shape}")
        return df
    except Exception as exc:
        logger.error(f"CSV parse error: {exc}")
        return None


def _bronze_from_parquet(path: Path) -> Optional[pd.DataFrame]:
    """Load existing Bronze parquet as-is."""
    if not path.exists():
        logger.warning(f"[BRONZE] Parquet not found: {path}")
        return None
    try:
        df = pd.read_parquet(str(path))
        logger.info(f"[BRONZE] Parquet loaded ✓  shape={df.shape}  path={path}")
        return df
    except Exception as exc:
        logger.error(f"Parquet read error: {exc}")
        return None


def bronze_extract(pb: Optional[PocketBaseClient]) -> pd.DataFrame:
    """
    BRONZE LAYER — Extract raw data.
    Priority: PocketBase CSV → local Bronze parquet.
    Saves a copy to BRONZE_DIR as raw_spotify.parquet (immutable raw layer).
    """
    logger.info("══ BRONZE: Extract ══════════════════════════════════════════")
    df: Optional[pd.DataFrame] = None

    if pb is not None:
        df = _bronze_from_pocketbase(pb)

    if df is None or df.empty:
        df = _bronze_from_parquet(BRONZE_PARQUET)

    if df is None or df.empty:
        raise RuntimeError(
            "BRONZE EXTRACT FAILED — no data source available.\n"
            f"  • PocketBase : {POCKETBASE_URL}  (check credentials)\n"
            f"  • Local Bronze: {BRONZE_PARQUET}  (file missing)"
        )

    # Persist raw copy to bronze (only if it came from PocketBase)
    if pb is not None:
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(str(BRONZE_PARQUET), index=False)
        logger.info(f"[BRONZE] Saved raw parquet → {BRONZE_PARQUET}")

    logger.info(f"[BRONZE] {len(df):,} rows, {len(df.columns)} columns")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
#  SILVER LAYER — Clean, normalize, deduplicate
#  Goal: produce a reliable, typed, deduplicated parquet in data/silver/
# ═══════════════════════════════════════════════════════════════════════════════

# Column rename map: source column names → canonical names
_COLUMN_MAP: Dict[str, str] = {
    "track_id":        "track_id",
    "id":              "track_id",   # only if no track_id present
    "track_name":      "track_name",
    "name":            "track_name",
    "artists":         "artists",
    "artist_name":     "artists",
    "artist":          "artists",
    "album_name":      "album_name",
    "album":           "album_name",
    "popularity":      "popularity",
    "duration_ms":     "duration_ms",
    "explicit":        "explicit",
    "danceability":    "danceability",
    "energy":          "energy",
    "key":             "key_col",
    "key_col":         "key_col",
    "loudness":        "loudness",
    "mode":            "mode_col",
    "mode_col":        "mode_col",
    "speechiness":     "speechiness",
    "acousticness":    "acousticness",
    "instrumentalness":"instrumentalness",
    "liveness":        "liveness",
    "valence":         "valence",
    "tempo":           "tempo",
    "time_signature":  "time_signature",
    "track_genre":     "track_genre",
    "genre":           "track_genre",
}

_FLOAT_COLS = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
]
_INT_COLS = ["key_col", "mode_col", "time_signature", "popularity", "duration_ms"]

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


def _clean_str(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    return s.replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "None": pd.NA, "NaN": pd.NA})


def silver_transform(df_bronze: pd.DataFrame) -> pd.DataFrame:
    """
    SILVER LAYER — Clean and normalize the Bronze DataFrame.
    - Rename columns to canonical names
    - Coerce types
    - Fill nulls with safe defaults
    - Deduplicate on track_id
    - Drop rows with null track_name (critical FK)
    Saves output to data/silver/silver_spotify.parquet
    """
    logger.info("══ SILVER: Transform ════════════════════════════════════════")
    df = df_bronze.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Build rename map (don't let bare 'id' overwrite existing 'track_id')
    rename_map: Dict[str, str] = {}
    for col in df.columns:
        if col in _COLUMN_MAP:
            target = _COLUMN_MAP[col]
            if col == "id" and "track_id" in df.columns:
                continue
            rename_map[col] = target
    df.rename(columns=rename_map, inplace=True)

    # Drop duplicate column names (keep first)
    df = df.loc[:, ~df.columns.duplicated()]

    # Add any missing canonical columns
    for col, default in _RAW_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default

    # Clean string columns
    for col in ("track_id", "track_name", "artists", "album_name", "track_genre"):
        if col in df.columns:
            df[col] = _clean_str(df[col])

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
    df["explicit"] = df["explicit"].fillna(False).astype(bool)

    # Drop rows where track_name is null (NOT NULL constraint on dim_track)
    before = len(df)
    df = df[df["track_name"].notna() & (df["track_name"].str.strip() != "")]
    dropped = before - len(df)
    if dropped:
        logger.warning(f"[SILVER] Dropped {dropped:,} rows with null/empty track_name")

    # Deduplicate on track_id (keep first occurrence)
    if df["track_id"].notna().any():
        df = df.drop_duplicates(subset=["track_id"], keep="first")

    df = df.reset_index(drop=True)

    logger.info(f"[SILVER] {len(df):,} rows after cleaning")

    # Persist Silver layer
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(SILVER_PARQUET), index=False)
    logger.info(f"[SILVER] Saved → {SILVER_PARQUET}")

    return df


# ═══════════════════════════════════════════════════════════════════════════════
#  DUCKDB — Connection helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _open_connection(db_path: Path, *, recreate: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Open DuckDB.  If file is corrupt/version-mismatched, back it up and
    recreate from scratch (happens when upgrading duckdb across major versions).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if recreate and db_path.exists():
        backup = db_path.with_suffix(
            f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.duckdb"
        )
        logger.warning(f"Moving corrupt DB → backup: {backup}")
        shutil.move(str(db_path), str(backup))
        wal = Path(str(db_path) + ".wal")
        if wal.exists():
            wal.unlink()

    try:
        conn = duckdb.connect(str(db_path), read_only=False)
        conn.execute("SELECT 1").fetchone()  # smoke test
        logger.info(f"DuckDB connected: {db_path}")
        return conn
    except Exception as exc:
        err_str = str(exc).lower()
        if any(kw in err_str for kw in ("serial", "deserial", "incompatible", "version")):
            if not recreate:
                logger.warning(f"DuckDB version error: {exc}\n  → Recreating DB…")
                return _open_connection(db_path, recreate=True)
        raise RuntimeError(f"Cannot open DuckDB at {db_path}: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════════
#  GOLD LAYER — DDL (schema)
#  Full dimensional model required by the FastAPI backend
# ═══════════════════════════════════════════════════════════════════════════════

DDL_STATEMENTS: List[str] = [

    # ── Control / audit ────────────────────────────────────────────────────
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

    # ── Bronze staging (mirror of raw data inside DuckDB) ──────────────────
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

    # ── DIMENSIONS ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS dim_usuario (
        id_usuario    INTEGER PRIMARY KEY,
        nombre        VARCHAR NOT NULL,
        email         VARCHAR,
        pais          VARCHAR,
        plan          VARCHAR DEFAULT 'free',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
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
        duration_ms      INTEGER,
        danceability     DOUBLE,
        energy           DOUBLE,
        loudness         DOUBLE,
        speechiness      DOUBLE,
        acousticness     DOUBLE,
        instrumentalness DOUBLE,
        liveness         DOUBLE,
        valence          DOUBLE,
        tempo            DOUBLE,
        popularity       INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_playlist (
        id_playlist    INTEGER PRIMARY KEY,
        nombre         VARCHAR NOT NULL,
        id_usuario     INTEGER,
        descripcion    VARCHAR,
        publica        BOOLEAN DEFAULT TRUE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_tiempo (
        id_tiempo  INTEGER PRIMARY KEY,
        fecha      DATE NOT NULL UNIQUE,
        anio       INTEGER NOT NULL,
        mes        INTEGER NOT NULL,
        dia        INTEGER NOT NULL,
        trimestre  INTEGER NOT NULL,
        dia_semana INTEGER NOT NULL,
        nombre_mes VARCHAR NOT NULL,
        es_fin_semana BOOLEAN NOT NULL
    )
    """,

    # ── FACT TABLE ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS fact_streaming (
        id_streaming  INTEGER PRIMARY KEY,
        id_track      INTEGER NOT NULL,
        id_usuario    INTEGER,
        id_tiempo     INTEGER,
        id_playlist   INTEGER,
        streams       INTEGER DEFAULT 1,
        duracion_ms   INTEGER,
        completado    BOOLEAN DEFAULT TRUE,
        fecha_evento  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # ── AGGREGATIONS (Gold analytical layer) ───────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS agg_top_artistas (
        id_artista           INTEGER PRIMARY KEY,
        nombre_artista       VARCHAR,
        promedio_popularidad DOUBLE,
        total_tracks         INTEGER,
        total_streams        INTEGER DEFAULT 0
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
    """
    CREATE TABLE IF NOT EXISTS agg_tracks_populares (
        id_track             INTEGER PRIMARY KEY,
        nombre_track         VARCHAR,
        nombre_artista       VARCHAR,
        nombre_album         VARCHAR,
        nombre_genero        VARCHAR,
        popularity           INTEGER,
        energy               DOUBLE,
        danceability         DOUBLE,
        valence              DOUBLE,
        tempo                DOUBLE,
        duration_ms          INTEGER
    )
    """,
]


def apply_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all tables idempotently."""
    for ddl in DDL_STATEMENTS:
        try:
            conn.execute(ddl)
        except Exception as exc:
            logger.error(f"DDL failed:\n{ddl.strip()}\nError: {exc}")
            raise
    logger.info("[GOLD] Schema applied ✓")


# ═══════════════════════════════════════════════════════════════════════════════
#  GOLD LAYER — Load Silver data into DuckDB staging (raw_spotify)
# ═══════════════════════════════════════════════════════════════════════════════

def gold_load_staging(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    """
    Load the Silver DataFrame into the raw_spotify staging table in DuckDB.
    Returns the number of rows loaded.
    """
    logger.info("══ GOLD: Load staging ═══════════════════════════════════════")

    raw_cols = list(_RAW_DEFAULTS.keys())
    available = [c for c in raw_cols if c in df.columns]
    df_load   = df[available].copy().reset_index(drop=True)
    df_load.insert(0, "id", range(1, len(df_load) + 1))

    conn.execute("DELETE FROM raw_spotify")
    conn.register("_df_staging", df_load)
    cols_sql = ", ".join(available)
    conn.execute(f"""
        INSERT INTO raw_spotify (id, {cols_sql})
        SELECT id, {cols_sql} FROM _df_staging
    """)
    conn.unregister("_df_staging")

    count = conn.execute("SELECT COUNT(*) FROM raw_spotify").fetchone()[0]
    logger.info(f"[GOLD] raw_spotify (staging) → {count:,} rows")
    return count


# ═══════════════════════════════════════════════════════════════════════════════
#  GOLD LAYER — Build dimensional model from staging
# ═══════════════════════════════════════════════════════════════════════════════

def _build_dim_tiempo(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Populate dim_tiempo with one row per calendar date spanning the dataset
    plus a reasonable range for synthetic streaming events.
    Generates dates from 2020-01-01 to today.
    """
    conn.execute("DELETE FROM dim_tiempo")

    # Use DuckDB's generate_series to create a date spine
    conn.execute("""
        INSERT INTO dim_tiempo (
            id_tiempo, fecha, anio, mes, dia,
            trimestre, dia_semana, nombre_mes, es_fin_semana
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY d.fecha)   AS id_tiempo,
            d.fecha,
            YEAR(d.fecha)                          AS anio,
            MONTH(d.fecha)                         AS mes,
            DAY(d.fecha)                           AS dia,
            QUARTER(d.fecha)                       AS trimestre,
            DAYOFWEEK(d.fecha)                     AS dia_semana,
            MONTHNAME(d.fecha)                     AS nombre_mes,
            DAYOFWEEK(d.fecha) IN (1, 7)           AS es_fin_semana
        FROM (
            SELECT CAST(range AS DATE) AS fecha
            FROM range(
                DATE '2020-01-01',
                CURRENT_DATE + INTERVAL '1' DAY,
                INTERVAL '1' DAY
            )
        ) d
    """)
    n = conn.execute("SELECT COUNT(*) FROM dim_tiempo").fetchone()[0]
    logger.info(f"[GOLD] dim_tiempo      → {n:,} rows")


def _build_dim_usuario(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Seed dim_usuario with a synthetic default user so fact_streaming FKs are valid.
    Real user management happens via PocketBase / FastAPI auth.
    """
    conn.execute("DELETE FROM dim_usuario")
    conn.execute("""
        INSERT INTO dim_usuario (id_usuario, nombre, email, pais, plan)
        VALUES (1, 'Usuario Anónimo', 'anon@voxmetrik.io', 'EC', 'free')
    """)
    logger.info("[GOLD] dim_usuario     → 1 row (seed)")


def _build_dim_artista(conn: duckdb.DuckDBPyConnection) -> None:
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
    logger.info(f"[GOLD] dim_artista     → {n:,} rows")


def _build_dim_genero(conn: duckdb.DuckDBPyConnection) -> None:
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
    logger.info(f"[GOLD] dim_genero      → {n:,} rows")


def _build_dim_album(conn: duckdb.DuckDBPyConnection) -> None:
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
    logger.info(f"[GOLD] dim_album       → {n:,} rows")


def _build_dim_track(conn: duckdb.DuckDBPyConnection) -> None:
    """
    dim_track includes audio features inline so the backend can query
    track details without joining to a separate fact table.
    """
    conn.execute("DELETE FROM dim_track")
    conn.execute("""
        INSERT INTO dim_track (
            id_track, spotify_track_id, nombre_track,
            id_artista, id_album, id_genero, explicit, duration_ms,
            danceability, energy, loudness, speechiness, acousticness,
            instrumentalness, liveness, valence, tempo, popularity
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY rs.id)                           AS id_track,
            rs.track_id                                                   AS spotify_track_id,
            COALESCE(NULLIF(TRIM(rs.track_name), ''), 'Unknown Track')   AS nombre_track,
            da.id_artista,
            dal.id_album,
            dg.id_genero,
            rs.explicit,
            rs.duration_ms,
            COALESCE(rs.danceability,     0.0),
            COALESCE(rs.energy,           0.0),
            COALESCE(rs.loudness,         0.0),
            COALESCE(rs.speechiness,      0.0),
            COALESCE(rs.acousticness,     0.0),
            COALESCE(rs.instrumentalness, 0.0),
            COALESCE(rs.liveness,         0.0),
            COALESCE(rs.valence,          0.0),
            COALESCE(rs.tempo,            0.0),
            COALESCE(rs.popularity,       0)
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
        LEFT JOIN dim_genero  dg  ON dg.nombre_genero  = TRIM(COALESCE(rs.track_genre,''))
        WHERE rs.rn = 1
    """)
    n = conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0]
    logger.info(f"[GOLD] dim_track       → {n:,} rows")


def _build_dim_playlist(conn: duckdb.DuckDBPyConnection) -> None:
    """Seed a default playlist; real playlists come from the application layer."""
    conn.execute("DELETE FROM dim_playlist")
    conn.execute("""
        INSERT INTO dim_playlist (id_playlist, nombre, id_usuario, descripcion, publica)
        VALUES (1, 'Top Tracks', 1, 'Playlist generada automáticamente', TRUE)
    """)
    logger.info("[GOLD] dim_playlist    → 1 row (seed)")


def _build_fact_streaming(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Build fact_streaming.
    Each track gets one synthetic streaming event assigned to the most recent
    date in dim_tiempo.  Real streaming events are appended by the application.
    """
    conn.execute("DELETE FROM fact_streaming")

    # Get most recent date id for synthetic events
    max_tiempo = conn.execute(
        "SELECT id_tiempo FROM dim_tiempo ORDER BY fecha DESC LIMIT 1"
    ).fetchone()
    id_tiempo_default = max_tiempo[0] if max_tiempo else 1

    conn.execute(f"""
        INSERT INTO fact_streaming (
            id_streaming, id_track, id_usuario, id_tiempo,
            id_playlist, streams, duracion_ms, completado
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY dt.id_track) AS id_streaming,
            dt.id_track,
            1                                        AS id_usuario,
            {id_tiempo_default}                      AS id_tiempo,
            1                                        AS id_playlist,
            COALESCE(dt.popularity, 1)               AS streams,
            dt.duration_ms,
            TRUE
        FROM dim_track dt
    """)
    n = conn.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0]
    logger.info(f"[GOLD] fact_streaming  → {n:,} rows")


# ── Aggregations ──────────────────────────────────────────────────────────────

def _build_agg_top_artistas(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM agg_top_artistas")
    conn.execute("""
        INSERT INTO agg_top_artistas (
            id_artista, nombre_artista,
            promedio_popularidad, total_tracks, total_streams
        )
        SELECT
            da.id_artista,
            da.nombre_artista,
            ROUND(AVG(CAST(COALESCE(dt.popularity, 0) AS DOUBLE)), 2) AS promedio_popularidad,
            COUNT(dt.id_track)                                         AS total_tracks,
            COALESCE(SUM(fs.streams), 0)                               AS total_streams
        FROM dim_artista da
        LEFT JOIN dim_track     dt ON dt.id_artista = da.id_artista
        LEFT JOIN fact_streaming fs ON fs.id_track  = dt.id_track
        GROUP BY da.id_artista, da.nombre_artista
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_top_artistas").fetchone()[0]
    logger.info(f"[GOLD] agg_top_artistas → {n:,} rows")


def _build_agg_genero_popularidad(conn: duckdb.DuckDBPyConnection) -> None:
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
            ROUND(AVG(CAST(COALESCE(dt.popularity, 0) AS DOUBLE)), 2) AS popularidad_promedio,
            ROUND(AVG(CAST(COALESCE(dt.energy,     0) AS DOUBLE)), 3) AS energia_promedio,
            COUNT(dt.id_track)                                         AS total_tracks,
            COUNT(DISTINCT dt.id_artista)                              AS total_artistas
        FROM dim_genero dg
        LEFT JOIN dim_track dt ON dt.id_genero = dg.id_genero
        GROUP BY dg.id_genero, dg.nombre_genero
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_genero_popularidad").fetchone()[0]
    logger.info(f"[GOLD] agg_genero_pop  → {n:,} rows")


def _build_agg_distribucion_energia(conn: duckdb.DuckDBPyConnection) -> None:
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
        FROM dim_track
        WHERE energy IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_distribucion_energia").fetchone()[0]
    logger.info(f"[GOLD] agg_dist_energy → {n:,} rows")


def _build_agg_tracks_populares(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DELETE FROM agg_tracks_populares")
    conn.execute("""
        INSERT INTO agg_tracks_populares (
            id_track, nombre_track, nombre_artista,
            nombre_album, nombre_genero, popularity,
            energy, danceability, valence, tempo, duration_ms
        )
        SELECT
            dt.id_track,
            dt.nombre_track,
            da.nombre_artista,
            dal.nombre_album,
            dg.nombre_genero,
            dt.popularity,
            dt.energy,
            dt.danceability,
            dt.valence,
            dt.tempo,
            dt.duration_ms
        FROM dim_track dt
        LEFT JOIN dim_artista da  ON da.id_artista = dt.id_artista
        LEFT JOIN dim_album   dal ON dal.id_album  = dt.id_album
        LEFT JOIN dim_genero  dg  ON dg.id_genero  = dt.id_genero
    """)
    n = conn.execute("SELECT COUNT(*) FROM agg_tracks_populares").fetchone()[0]
    logger.info(f"[GOLD] agg_tracks_pop  → {n:,} rows")


def gold_build_warehouse(conn: duckdb.DuckDBPyConnection) -> None:
    """
    GOLD LAYER — Build full dimensional model in dependency order.
    Order matters: dimensions must exist before fact table.
    """
    logger.info("══ GOLD: Build warehouse ════════════════════════════════════")
    _build_dim_tiempo(conn)
    _build_dim_usuario(conn)
    _build_dim_artista(conn)
    _build_dim_genero(conn)
    _build_dim_album(conn)
    _build_dim_track(conn)
    _build_dim_playlist(conn)
    _build_fact_streaming(conn)
    _build_agg_top_artistas(conn)
    _build_agg_genero_popularidad(conn)
    _build_agg_distribucion_energia(conn)
    _build_agg_tracks_populares(conn)
    logger.info("[GOLD] Warehouse build complete ✓")


# ── Also export Silver Parquet snapshots of Gold tables ──────────────────────

def _export_gold_parquets(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Optionally export key Gold tables as Parquet to data/gold/ for BI tools
    or downstream consumers that don't speak DuckDB.
    """
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    tables = [
        "dim_artista", "dim_genero", "dim_album", "dim_track",
        "dim_tiempo", "dim_usuario", "dim_playlist",
        "fact_streaming",
        "agg_top_artistas", "agg_genero_popularidad",
        "agg_distribucion_energia", "agg_tracks_populares",
    ]
    for table in tables:
        out = GOLD_DIR / f"{table}.parquet"
        try:
            conn.execute(f"COPY {table} TO '{out}' (FORMAT PARQUET)")
            logger.info(f"[GOLD] Exported {table} → {out.name}")
        except Exception as exc:
            logger.warning(f"[GOLD] Export {table} skipped: {exc}")


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
#  VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def verify_warehouse(conn: duckdb.DuckDBPyConnection) -> bool:
    """
    Verify that all required tables exist and have data.
    Returns True if all checks pass.
    """
    logger.info("══ VERIFY ═══════════════════════════════════════════════════")
    required = [
        "dim_usuario", "dim_artista", "dim_genero", "dim_album",
        "dim_track", "dim_playlist", "dim_tiempo", "fact_streaming",
    ]
    all_ok = True
    for table in required:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            status = "✓" if count > 0 else "⚠ EMPTY"
            logger.info(f"  {table:<25} {count:>8,} rows  {status}")
            if count == 0:
                all_ok = False
        except Exception as exc:
            logger.error(f"  {table:<25} MISSING  ✗  ({exc})")
            all_ok = False

    if all_ok:
        logger.info("[VERIFY] All required tables present and populated ✓")
    else:
        logger.warning("[VERIFY] Some tables are missing or empty ⚠")

    return all_ok


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline() -> None:
    start = datetime.now()
    logger.info("=" * 70)
    logger.info("  VOXMETRIK_V2 — ELT Pipeline (Medallion Architecture)")
    logger.info(f"  Started : {start:%Y-%m-%d %H:%M:%S}")
    logger.info(f"  DB_PATH : {DB_PATH}")
    logger.info(f"  Bronze  : {BRONZE_PARQUET}")
    logger.info(f"  Silver  : {SILVER_PARQUET}")
    logger.info(f"  Gold    : {GOLD_DIR}")
    logger.info("=" * 70)

    # ── PocketBase (optional) ─────────────────────────────────────────────────
    pb: Optional[PocketBaseClient] = None
    if POCKETBASE_EMAIL and POCKETBASE_PASSWORD:
        pb = PocketBaseClient(POCKETBASE_URL, POCKETBASE_EMAIL, POCKETBASE_PASSWORD)
        if not pb.authenticate():
            logger.warning("PocketBase unavailable — will use local parquet")
            pb = None
    else:
        logger.info("PocketBase credentials not set — using local parquet")

    # ── Open DuckDB ──────────────────────────────────────────────────────────
    conn = _open_connection(DB_PATH)

    try:
        # ── Apply schema ─────────────────────────────────────────────────────
        apply_schema(conn)

        # ── BRONZE: Extract ──────────────────────────────────────────────────
        df_bronze = bronze_extract(pb)

        # ── SILVER: Clean ────────────────────────────────────────────────────
        df_silver = silver_transform(df_bronze)

        # ── GOLD: Load staging ───────────────────────────────────────────────
        total_raw = gold_load_staging(conn, df_silver)

        # ── GOLD: Build dimensional model ────────────────────────────────────
        gold_build_warehouse(conn)

        # ── GOLD: Export Parquet snapshots ───────────────────────────────────
        _export_gold_parquets(conn)

        # ── Verify ───────────────────────────────────────────────────────────
        verify_warehouse(conn)

        # ── Register success ─────────────────────────────────────────────────
        _register_load(conn, "FULL", total_raw, total_raw, "EXITOSO")
        _audit(conn, "ELT_PIPELINE", "all", f"OK rows={total_raw}")
        conn.commit()

        elapsed = (datetime.now() - start).total_seconds()
        logger.info("=" * 70)
        logger.info(f"  Pipeline SUCCESS ✓  ({elapsed:.1f}s)")
        logger.info(f"  Warehouse  : {DB_PATH}")
        logger.info(f"  Rows loaded: {total_raw:,}")
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