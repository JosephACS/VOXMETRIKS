import duckdb

# Conexión a DuckDB
conn = duckdb.connect("duckdb/voxmetrik.duckdb")

# Obtener tablas
tables = conn.execute("SHOW TABLES").fetchall()

schema_output = []

for table in tables:
    table_name = table[0]

    schema_output.append(f"\n-- TABLE: {table_name}\n")

    describe = conn.execute(f"DESCRIBE {table_name}").fetchall()

    schema_output.append(f"CREATE TABLE {table_name} (\n")

    columns = []

    for col in describe:
        col_name = col[0]
        col_type = col[1]
        nullable = col[2]

        line = f"    {col_name} {col_type}"

        if nullable == "NO":
            line += " NOT NULL"

        columns.append(line)

    schema_output.append(",\n".join(columns))
    schema_output.append("\n);\n")

# Guardar schema.sql
with open("schema.sql", "w", encoding="utf-8") as f:
    f.write("".join(schema_output))

print("✅ schema.sql generado correctamente")