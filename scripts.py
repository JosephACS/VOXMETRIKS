import duckdb

conn = duckdb.connect("duckdb/voxmetrik.duckdb")

tables = conn.execute("SHOW TABLES").fetchall()

with open("schema_dump.txt", "w", encoding="utf-8") as f:
    for table in tables:
        table_name = table[0]

        f.write(f"\n{'='*80}\n")
        f.write(f"TABLE: {table_name}\n")
        f.write(f"{'='*80}\n\n")

        schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()

        f.write(schema.to_string())
        f.write("\n\n")

print("✅ Schema exportado a schema_dump.txt")