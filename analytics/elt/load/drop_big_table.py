import duckdb

con = duckdb.connect("duckdb/voxmetrik.duckdb")

print("Eliminando tabla spotify_big_data...")

con.execute("""
DROP TABLE IF EXISTS spotify_big_data
""")

print("Tabla eliminada correctamente.")

con.close()