import duckdb

conn = duckdb.connect("duckdb/voxmetrik.duckdb")

query = """
SELECT *
FROM agg_top_artistas
LIMIT 10;
"""

result = conn.execute(query).fetchdf()

print(result)