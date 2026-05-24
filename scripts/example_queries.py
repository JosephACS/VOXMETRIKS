#!/usr/bin/env python3
"""
VOXMETRIK_V2 - Ejemplos de Consultas Avanzadas
==============================================

Script con ejemplos de consultas SQL avanzadas para análisis musical
usando el Data Warehouse de VOXMETRIK_V2.

Uso:
    python example_queries.py
"""

import duckdb
from pathlib import Path


class WarehouseQueries:
    """Colección de consultas avanzadas para análisis."""
    
    def __init__(self, db_path: str = "duckdb/voxmetrik.duckdb"):
        """Inicializar conexión."""
        self.conn = duckdb.connect(db_path)
        print(f"✓ Conectado a: {db_path}\n")
    
    def query_1_canciones_mas_bailables(self):
        """Consulta 1: Canciones más bailables (danceability > 0.7)."""
        print("=" * 80)
        print("CONSULTA 1: CANCIONES MÁS BAILABLES (Danceability > 0.7)")
        print("=" * 80)
        
        query = """
        SELECT 
            dt.nombre_track as cancion,
            da.nombre_artista as artista,
            ROUND(faf.danceability, 3) as bailabilidad,
            faf.tempo as tempo_bpm,
            faf.popularity as popularidad
        FROM fact_audio_features faf
        INNER JOIN dim_track dt ON faf.id_track = dt.id_track
        INNER JOIN dim_album da ON dt.id_album = da.id_album
        WHERE faf.danceability > 0.7
        ORDER BY faf.danceability DESC
        """
        
        result = self.conn.execute(query).fetchall()
        for row in result:
            print(f"  • {row[0]:30s} | {row[1]:15s} | "
                  f"Bailabilidad: {row[2]:.3f} | Tempo: {row[3]:.1f} BPM | "
                  f"Popularidad: {row[4]}")
        print()
    
    def query_2_correlacion_energia_tempo(self):
        """Consulta 2: Correlación entre energía y tempo."""
        print("=" * 80)
        print("CONSULTA 2: CORRELACIÓN ENERGÍA-TEMPO (Promedio por rango)")
        print("=" * 80)
        
        query = """
        WITH energia_clasificada AS (
            SELECT 
                CASE 
                    WHEN faf.energy < 0.33 THEN 'Baja Energía'
                    WHEN faf.energy < 0.66 THEN 'Energía Media'
                    ELSE 'Alta Energía'
                END as clasificacion,
                faf.tempo,
                faf.energy
            FROM fact_audio_features faf
        )
        SELECT 
            clasificacion,
            COUNT(*) as cantidad_tracks,
            ROUND(AVG(tempo), 2) as tempo_promedio,
            ROUND(AVG(energy), 3) as energia_promedio,
            ROUND(MIN(tempo), 2) as tempo_minimo,
            ROUND(MAX(tempo), 2) as tempo_maximo
        FROM energia_clasificada
        GROUP BY clasificacion
        ORDER BY energia_promedio DESC
        """
        
        result = self.conn.execute(query).fetchall()
        for row in result:
            print(f"\n  {row[0]}:")
            print(f"    - Cantidad de tracks: {row[1]}")
            print(f"    - Tempo promedio: {row[2]} BPM")
            print(f"    - Energía promedio: {row[3]}")
            print(f"    - Rango tempo: {row[4]} - {row[5]} BPM")
        print()
    
    def query_3_genero_mas_acustico(self):
        """Consulta 3: Géneros más acústicos."""
        print("=" * 80)
        print("CONSULTA 3: GÉNEROS MÁS ACÚSTICOS (Top 5)")
        print("=" * 80)
        
        query = """
        SELECT 
            dg.nombre_genero as genero,
            COUNT(DISTINCT faf.id_track) as total_tracks,
            ROUND(AVG(faf.acousticness), 3) as acusticidad_promedio,
            ROUND(AVG(faf.popularity), 2) as popularidad_promedio
        FROM fact_audio_features faf
        INNER JOIN dim_track dt ON faf.id_track = dt.id_track
        CROSS JOIN dim_genero dg
        GROUP BY dg.nombre_genero
        ORDER BY acusticidad_promedio DESC
        LIMIT 5
        """
        
        result = self.conn.execute(query).fetchall()
        for row in result:
            print(f"  • {row[0]:20s} | Tracks: {row[1]:3d} | "
                  f"Acusticidad: {row[2]:.3f} | Popularidad: {row[3]:.2f}")
        print()
    
    def query_4_artistas_multigenero(self):
        """Consulta 4: Artistas con música en múltiples géneros."""
        print("=" * 80)
        print("CONSULTA 4: ARTISTAS CON MÚLTIPLES GÉNEROS")
        print("=" * 80)
        
        query = """
        WITH artista_generos AS (
            SELECT 
                da.nombre_artista,
                COUNT(DISTINCT dg.id_genero) as cantidad_generos,
                ARRAY_AGG(DISTINCT dg.nombre_genero) as generos
            FROM dim_artista da
            INNER JOIN dim_album db ON da.id_artista = db.id_artista
            INNER JOIN dim_track dt ON db.id_album = dt.id_album
            CROSS JOIN dim_genero dg
            GROUP BY da.nombre_artista
            HAVING COUNT(DISTINCT dg.id_genero) > 1
        )
        SELECT 
            nombre_artista,
            cantidad_generos,
            generos
        FROM artista_generos
        ORDER BY cantidad_generos DESC
        """
        
        result = self.conn.execute(query).fetchall()
        for row in result:
            generos_str = ", ".join(row[2]) if row[2] else "N/A"
            print(f"  • {row[0]:20s} | Géneros: {row[1]} | {generos_str}")
        print()
    
    def query_5_tracks_instrumentales(self):
        """Consulta 5: Tracks mayormente instrumentales."""
        print("=" * 80)
        print("CONSULTA 5: TRACKS PRINCIPALMENTE INSTRUMENTALES")
        print("=" * 80)
        
        query = """
        SELECT 
            dt.nombre_track as cancion,
            da.nombre_artista as artista,
            ROUND(faf.instrumentalness, 3) as instrumentalidad,
            faf.duration_ms / 1000 as duracion_segundos,
            faf.popularity
        FROM fact_audio_features faf
        INNER JOIN dim_track dt ON faf.id_track = dt.id_track
        INNER JOIN dim_album da ON dt.id_album = da.id_album
        WHERE faf.instrumentalness > 0.5
        ORDER BY faf.instrumentalness DESC
        """
        
        result = self.conn.execute(query).fetchall()
        if result:
            for row in result:
                print(f"  • {row[0]:30s} | {row[1]:15s} | "
                      f"Instrumental: {row[2]:.3f} | "
                      f"Duración: {row[3]:.0f}s | Popularidad: {row[4]}")
        else:
            print("  No hay tracks instrumentales significativos en los datos.")
        print()
    
    def query_6_analisis_valence(self):
        """Consulta 6: Análisis de positividad (Valence)."""
        print("=" * 80)
        print("CONSULTA 6: ANÁLISIS DE POSITIVIDAD (VALENCE)")
        print("=" * 80)
        
        query = """
        WITH valence_clasificado AS (
            SELECT 
                CASE 
                    WHEN faf.valence < 0.33 THEN 'Negativa'
                    WHEN faf.valence < 0.66 THEN 'Neutral'
                    ELSE 'Positiva'
                END as sentimiento,
                faf.valence,
                faf.popularity,
                faf.energy
            FROM fact_audio_features faf
        )
        SELECT 
            sentimiento,
            COUNT(*) as cantidad_tracks,
            ROUND(AVG(popularity), 2) as popularidad_promedio,
            ROUND(AVG(energy), 3) as energia_promedio,
            ROUND(AVG(valence), 3) as valence_promedio
        FROM valence_clasificado
        GROUP BY sentimiento
        ORDER BY valence_promedio DESC
        """
        
        result = self.conn.execute(query).fetchall()
        for row in result:
            print(f"\n  {row[0]} (Valence {row[4]:.3f}):")
            print(f"    - Tracks: {row[1]}")
            print(f"    - Popularidad promedio: {row[2]:.2f}")
            print(f"    - Energía promedio: {row[3]:.3f}")
        print()
    
    def query_7_ranking_albumes(self):
        """Consulta 7: Ranking de álbumes por calificación promedio."""
        print("=" * 80)
        print("CONSULTA 7: TOP 5 ÁLBUMES (por popularidad promedio)")
        print("=" * 80)
        
        query = """
        SELECT 
            da.nombre_album as album,
            dar.nombre_artista as artista,
            COUNT(DISTINCT dt.id_track) as total_tracks,
            ROUND(AVG(faf.popularity), 2) as popularidad_promedio,
            ROUND(AVG(faf.energy), 3) as energia_promedio
        FROM dim_album da
        INNER JOIN dim_artista dar ON da.id_artista = dar.id_artista
        INNER JOIN dim_track dt ON da.id_album = dt.id_album
        LEFT JOIN fact_audio_features faf ON dt.id_track = faf.id_track
        GROUP BY da.nombre_album, dar.nombre_artista
        ORDER BY popularidad_promedio DESC
        LIMIT 5
        """
        
        result = self.conn.execute(query).fetchall()
        for idx, row in enumerate(result, 1):
            print(f"\n  {idx}. {row[0]} - {row[1]}")
            print(f"     Tracks: {row[2]} | Popularidad: {row[3]:.2f} | "
                  f"Energía: {row[4]:.3f}")
        print()
    
    def query_8_hits_vs_floops(self):
        """Consulta 8: Hits vs Flops (análisis de popularidad)."""
        print("=" * 80)
        print("CONSULTA 8: ANÁLISIS HITS vs FLOPS")
        print("=" * 80)
        
        query = """
        WITH popularity_classified AS (
            SELECT 
                CASE 
                    WHEN faf.popularity >= 80 THEN 'HIT'
                    WHEN faf.popularity >= 50 THEN 'ESTABLE'
                    ELSE 'BAJO RENDIMIENTO'
                END as clasificacion,
                faf.popularity,
                faf.danceability,
                faf.energy,
                faf.valence
            FROM fact_audio_features faf
        )
        SELECT 
            clasificacion,
            COUNT(*) as cantidad,
            ROUND(AVG(popularity), 2) as pop_promedio,
            ROUND(AVG(danceability), 3) as dance_promedio,
            ROUND(AVG(energy), 3) as energy_promedio,
            ROUND(AVG(valence), 3) as valence_promedio
        FROM popularity_classified
        GROUP BY clasificacion
        ORDER BY 
            CASE 
                WHEN clasificacion = 'HIT' THEN 1
                WHEN clasificacion = 'ESTABLE' THEN 2
                ELSE 3
            END
        """
        
        result = self.conn.execute(query).fetchall()
        for row in result:
            print(f"\n  {row[0]}:")
            print(f"    - Cantidad: {row[1]}")
            print(f"    - Popularidad promedio: {row[2]:.2f}")
            print(f"    - Bailabilidad: {row[3]:.3f}")
            print(f"    - Energía: {row[4]:.3f}")
            print(f"    - Positividad: {row[5]:.3f}")
        print()
    
    def run_all(self):
        """Ejecutar todas las consultas."""
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "EJEMPLOS DE CONSULTAS AVANZADAS - VOXMETRIK_V2".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        
        self.query_1_canciones_mas_bailables()
        self.query_2_correlacion_energia_tempo()
        self.query_3_genero_mas_acustico()
        self.query_4_artistas_multigenero()
        self.query_5_tracks_instrumentales()
        self.query_6_analisis_valence()
        self.query_7_ranking_albumes()
        self.query_8_hits_vs_floops()
        
        print("=" * 80)
        print("FIN DE LAS CONSULTAS DE EJEMPLO")
        print("=" * 80)
    
    def close(self):
        """Cerrar conexión."""
        if self.conn:
            self.conn.close()


def main():
    """Función principal."""
    try:
        db_path = "duckdb/voxmetrik.duckdb"
        
        # Verificar que la BD existe
        if not Path(db_path).exists():
            print(f"✗ Error: Base de datos no encontrada en {db_path}")
            print("  Ejecuta primero: python elt_pipeline.py")
            return
        
        # Ejecutar consultas
        queries = WarehouseQueries(db_path)
        queries.run_all()
        queries.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
