"""Quick warehouse validation after ELT run."""
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
GOLD = ROOT / "data" / "gold"

c = duckdb.connect(str(DB))
facts = [
    "fact_streaming", "fact_user_activity", "fact_playlist_activity",
    "fact_favorites", "fact_searches", "fact_stream_sessions",
]
print("=== FACT TABLES ===")
ft = 0
for t in facts:
    n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    ft += n
    print(f"  {t}: {n:,}")
print(f"  TOTAL FACTS: {ft:,}")

aggs = [r[0] for r in c.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='main' AND table_name LIKE 'agg_%' ORDER BY 1"
).fetchall()]
print(f"\n=== AGG TABLES ({len(aggs)}) ===")
for t in aggs:
    n = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n:,}")

print(f"\n=== DB SIZE: {DB.stat().st_size / (1024*1024):.1f} MB ===")
print(f"=== PARQUET FILES: {len(list(GOLD.glob('*.parquet')))} ===")
c.close()
