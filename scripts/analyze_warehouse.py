#!/usr/bin/env python3
"""
VOXMETRIK_V2 - Utilidades de Análisis y Validación
===================================================

Script auxiliar para consultar, validar y analizar el Data Warehouse
después de ejecutar el pipeline ELT.

Uso:
    python analyze_warehouse.py
"""

import duckdb
import sys
from pathlib import Path

# Intentar importar tabulate, si no existe usar alternativa
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    # Función alternativa simple
    def tabulate(data, headers=None, tablefmt="grid"):
        """Tabla simple sin tabulate."""
        if not data:
            return ""
        max_widths = [len(h) for h in (headers or [])]
        for row in data:
            for i, cell in enumerate(row):
                max_widths[i] = max(max_widths[i], len(str(cell)))
        
        output = []
        if headers:
            header_row = " | ".join(str(h).ljust(max_widths[i]) for i, h in enumerate(headers))
            output.append(header_row)
            output.append("-" * len(header_row))
        
        for row in data:
            output.append(" | ".join(str(cell).ljust(max_widths[i]) for i, cell in enumerate(row)))
        
        return "\n".join(output)


class WarehouseAnalyzer:
    """Analizador de Data Warehouse DuckDB."""
    
    def __init__(self, db_path: str | None = None):
        """Inicializar conexión a DuckDB."""
        root = Path(__file__).resolve().parents[1]
        self.db_path = Path(db_path) if db_path else root / "data" / "warehouse" / "voxmetrik.duckdb"
        self.conn = None
        self.connect()
    
    def connect(self) -> None:
        """Establecer conexión."""
        try:
            self.conn = duckdb.connect(str(self.db_path))
            print(f"✓ Conectado a: {self.db_path}\n")
        except Exception as e:
            print(f"✗ Error conectando: {e}")
            sys.exit(1)
    
    def get_table_stats(self) -> None:
        """Mostrar estadísticas de todas las tablas."""
        print("=" * 80)
        print("ESTADÍSTICAS DE TABLAS")
        print("=" * 80)
        
        query = """
        SELECT 
            table_name,
            COUNT(*) as registros
        FROM information_schema.tables t
        LEFT JOIN (
            SELECT table_name, COUNT(*) as cnt
            FROM information_schema.columns
            GROUP BY table_name
        ) c ON t.table_name = c.table_name
        WHERE table_schema = 'main'
        ORDER BY table_name
        """
        
        try:
            # Obtener todas las tablas
            tables = self.conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
            
            stats = []
            for (table_name,) in tables:
                try:
                    count = self.conn.execute(
                        f"SELECT COUNT(*) FROM {table_name}"
                    ).fetchone()[0]
                    stats.append([table_name, count])
                except:
                    stats.append([table_name, "ERROR"])
            
            print(tabulate(stats, headers=["Tabla", "Registros"], tablefmt="grid"))
            print()
        
        except Exception as e:
            print(f"Error: {e}\n")
    
    def show_top_artistas(self, limit: int = 10) -> None:
        """Mostrar top artistas por popularidad."""
        print("=" * 80)
        print(f"TOP {limit} ARTISTAS (por popularidad promedio)")
        print("=" * 80)
        
        query = f"""
        SELECT 
            da.nombre_artista,
            ata.promedio_popularidad,
            ata.total_tracks
        FROM agg_top_artistas ata
        JOIN dim_artista da ON ata.id_artista = da.id_artista
        ORDER BY promedio_popularidad DESC
        LIMIT {limit}
        """
        
        try:
            result = self.conn.execute(query).fetchall()
            if result:
                data = [[r[0], f"{r[1]:.2f}", r[2]] for r in result]
                print(tabulate(data, 
                    headers=["Artista", "Popularidad Promedio", "Total Tracks"],
                    tablefmt="grid"))
            else:
                print("No hay datos disponibles.")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
    
    def show_energy_distribution(self) -> None:
        """Mostrar distribución de energía."""
        print("=" * 80)
        print("DISTRIBUCIÓN DE ENERGÍA")
        print("=" * 80)
        
        query = """
        SELECT 
            rango_energia,
            cantidad_tracks,
            ROUND(100.0 * cantidad_tracks / SUM(cantidad_tracks) OVER (), 2) as porcentaje
        FROM agg_distribucion_energia
        ORDER BY 
            CASE 
                WHEN rango_energia = 'Baja' THEN 1
                WHEN rango_energia = 'Media' THEN 2
                ELSE 3
            END
        """
        
        try:
            result = self.conn.execute(query).fetchall()
            if result:
                data = [[r[0], r[1], f"{r[2]}%"] for r in result]
                print(tabulate(data,
                    headers=["Rango Energía", "Cantidad Tracks", "Porcentaje"],
                    tablefmt="grid"))
            else:
                print("No hay datos disponibles.")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
    
    def show_most_energetic_tracks(self, limit: int = 10) -> None:
        """Mostrar canciones más energéticas."""
        print("=" * 80)
        print(f"TOP {limit} CANCIONES MÁS ENERGÉTICAS")
        print("=" * 80)
        
        query = f"""
        SELECT 
            dt.nombre_track,
            da.nombre_artista,
            ROUND(faf.energy, 3) as energy,
            ROUND(faf.tempo, 2) as tempo,
            faf.popularity
        FROM fact_audio_features faf
        JOIN dim_track dt ON faf.id_track = dt.id_track
        JOIN dim_album da ON dt.id_album = da.id_album
        ORDER BY faf.energy DESC
        LIMIT {limit}
        """
        
        try:
            result = self.conn.execute(query).fetchall()
            if result:
                data = [[r[0][:30], r[1][:20], r[2], r[3], r[4]] for r in result]
                print(tabulate(data,
                    headers=["Track", "Artista", "Energy", "Tempo", "Popularity"],
                    tablefmt="grid"))
            else:
                print("No hay datos disponibles.")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
    
    def show_genre_stats(self) -> None:
        """Mostrar estadísticas por género."""
        print("=" * 80)
        print("ESTADÍSTICAS POR GÉNERO")
        print("=" * 80)
        
        query = """
        SELECT 
            dg.nombre_genero,
            agp.total_tracks,
            ROUND(agp.popularidad_promedio, 2) as popularidad_promedio,
            ROUND(agp.energia_promedio, 3) as energia_promedio
        FROM agg_genero_popularidad agp
        JOIN dim_genero dg ON agp.id_genero = dg.id_genero
        ORDER BY agp.total_tracks DESC
        """
        
        try:
            result = self.conn.execute(query).fetchall()
            if result:
                data = [[r[0], r[1], r[2], r[3]] for r in result]
                print(tabulate(data,
                    headers=["Género", "Total Tracks", "Popularidad Promedio", "Energía Promedio"],
                    tablefmt="grid"))
            else:
                print("No hay datos disponibles.")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
    
    def show_data_quality_report(self) -> None:
        """Mostrar reporte de calidad de datos."""
        print("=" * 80)
        print("REPORTE DE CALIDAD DE DATOS")
        print("=" * 80)
        
        checks = [
            ("Registros RAW", "SELECT COUNT(*) FROM raw_spotify"),
            ("Artistas únicos", "SELECT COUNT(*) FROM dim_artista"),
            ("Álbumes únicos", "SELECT COUNT(*) FROM dim_album"),
            ("Géneros únicos", "SELECT COUNT(*) FROM dim_genero"),
            ("Canciones", "SELECT COUNT(*) FROM dim_track"),
            ("Features de audio", "SELECT COUNT(*) FROM fact_audio_features"),
            ("Canciones con datos completos", 
             "SELECT COUNT(*) FROM fact_audio_features WHERE id_track IS NOT NULL"),
            ("Registros de carga", "SELECT COUNT(*) FROM ctl_carga_dataset"),
            ("Eventos de auditoría", "SELECT COUNT(*) FROM ctl_auditoria"),
        ]
        
        data = []
        for check_name, query in checks:
            try:
                result = self.conn.execute(query).fetchone()[0]
                data.append([check_name, result, "✓"])
            except Exception as e:
                data.append([check_name, "ERROR", "✗"])
        
        print(tabulate(data, headers=["Check", "Valor", "Estado"], tablefmt="grid"))
        print()
    
    def show_audit_log(self, limit: int = 10) -> None:
        """Mostrar registro de auditoría."""
        print("=" * 80)
        print(f"REGISTRO DE AUDITORÍA (últimos {limit})")
        print("=" * 80)
        
        query = f"""
        SELECT 
            id_auditoria,
            accion,
            tabla_afectada,
            fecha_evento,
            detalles
        FROM ctl_auditoria
        ORDER BY id_auditoria DESC
        LIMIT {limit}
        """
        
        try:
            result = self.conn.execute(query).fetchall()
            if result:
                data = [[r[0], r[1], r[2], str(r[3])[:19], r[4][:40]] for r in result]
                print(tabulate(data,
                    headers=["ID", "Acción", "Tabla", "Fecha", "Detalles"],
                    tablefmt="grid"))
            else:
                print("No hay registros de auditoría.")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
    
    def generate_full_report(self) -> None:
        """Generar reporte completo."""
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "ANÁLISIS COMPLETO DE DATA WAREHOUSE - VOXMETRIK_V2".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        
        self.get_table_stats()
        self.show_data_quality_report()
        self.show_top_artistas(10)
        self.show_energy_distribution()
        self.show_most_energetic_tracks(10)
        self.show_genre_stats()
        self.show_audit_log(5)
        
        print("=" * 80)
        print("FIN DEL REPORTE")
        print("=" * 80)
    
    def close(self) -> None:
        """Cerrar conexión."""
        if self.conn:
            self.conn.close()


def main():
    """Función principal."""
    try:
        analyzer = WarehouseAnalyzer()
        analyzer.generate_full_report()
        analyzer.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
