#!/usr/bin/env python
"""
Script de inicialización y verificación de VOXMETRIK_V2

Uso:
    python automation/scripts/init.py              # Verificación básica
    python automation/scripts/init.py --full       # Verificación completa
    python automation/scripts/init.py --info       # Información detallada
"""

import argparse
import logging
import os
import sys

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import check_database_health, get_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_file():
    """Verifica que el archivo de base de datos existe"""
    db_path = os.getenv("DB_PATH", "./duckdb/voxmetrik.duckdb")

    if not os.path.exists(db_path):
        logger.error(f"❌ Archivo de base de datos no encontrado: {db_path}")
        return False

    logger.info(f"✅ Archivo de base de datos encontrado: {db_path}")
    return True

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    try:
        conn = get_connection()
        result = conn.execute("SELECT 1").fetchall()
        logger.info("✅ Conexión a DuckDB establecida correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error al conectar a DuckDB: {str(e)}")
        return False

def check_tables():
    """Verifica que existen las tablas necesarias"""
    required_tables = {
        'dim_artista': 'Tabla de dimensión Artista',
        'dim_genero': 'Tabla de dimensión Género',
        'dim_track': 'Tabla de dimensión Track',
        'dim_album': 'Tabla de dimensión Album',
        'fact_audio_features': 'Tabla de hechos Audio Features',
        'agg_top_artistas': 'Tabla de agregación Top Artistas',
        'agg_genero_popularidad': 'Tabla de agregación Popularidad Género',
    }

    try:
        conn = get_connection()

        # Obtener lista de tablas
        result = conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
        """).fetch_df()

        existing_tables = set(result['table_name'].tolist())

        all_found = True
        for table_name, description in required_tables.items():
            if table_name in existing_tables:
                logger.info(f"✅ {description}: {table_name}")
            else:
                logger.warning(f"⚠️  {description}: {table_name} NO ENCONTRADA")
                all_found = False

        return all_found

    except Exception as e:
        logger.error(f"❌ Error verificando tablas: {str(e)}")
        return False

def check_data_integrity():
    """Verifica la integridad de los datos"""
    try:
        conn = get_connection()

        checks = {
            'dim_artista': "SELECT COUNT(*) as count FROM dim_artista",
            'dim_genero': "SELECT COUNT(*) as count FROM dim_genero",
            'dim_track': "SELECT COUNT(*) as count FROM dim_track",
            'dim_album': "SELECT COUNT(*) as count FROM dim_album",
            'fact_audio_features': "SELECT COUNT(*) as count FROM fact_audio_features",
        }

        logger.info("\n📊 Recuento de registros:")
        for table_name, query in checks.items():
            try:
                result = conn.execute(query).fetch_df()
                count = result['count'].iloc[0]
                logger.info(f"   {table_name}: {count:,} registros")
            except Exception as e:
                logger.warning(f"   {table_name}: Error - {str(e)}")

        return True

    except Exception as e:
        logger.error(f"❌ Error verificando integridad: {str(e)}")
        return False

def get_database_info():
    """Obtiene información detallada de la base de datos"""
    try:
        conn = get_connection()

        # Información general
        result = conn.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetch_df()

        logger.info("\n📋 Información de tablas:")
        for _, row in result.iterrows():
            logger.info(f"   {row['table_name']}: {row['column_count']} columnas")

        return True

    except Exception as e:
        logger.error(f"❌ Error obteniendo información: {str(e)}")
        return False

def basic_check():
    """Realiza una verificación básica"""
    logger.info("🔍 Iniciando verificación básica de VOXMETRIK_V2...\n")

    checks = [
        ("Archivo de BD", check_database_file),
        ("Conexión a BD", check_database_connection),
        ("Tablas requeridas", check_tables),
    ]

    results = []
    for check_name, check_func in checks:
        logger.info(f"\n🔎 Verificando {check_name}...")
        result = check_func()
        results.append((check_name, result))

    return all(result for _, result in results)

def full_check():
    """Realiza una verificación completa"""
    logger.info("🔍 Iniciando verificación COMPLETA de VOXMETRIK_V2...\n")

    checks = [
        ("Archivo de BD", check_database_file),
        ("Conexión a BD", check_database_connection),
        ("Tablas requeridas", check_tables),
        ("Integridad de datos", check_data_integrity),
    ]

    results = []
    for check_name, check_func in checks:
        logger.info(f"\n🔎 Verificando {check_name}...")
        result = check_func()
        results.append((check_name, result))

    return all(result for _, result in results)

def info_check():
    """Obtiene información detallada"""
    logger.info("ℹ️  Obteniendo información detallada de VOXMETRIK_V2...\n")

    health = check_database_health()
    logger.info(f"\n📊 Estado de la BD: {health['status']}")

    if health['status'] == 'healthy':
        logger.info(f"   Ruta: {health['database_path']}")
        logger.info(f"   Tablas: {health['tables_count']}")
        logger.info("   Lista de tablas:")
        for table in health['tables']:
            logger.info(f"      - {table}")
    else:
        logger.error(f"   Error: {health.get('error', 'Desconocido')}")

    get_database_info()

def main():
    parser = argparse.ArgumentParser(
        description='Script de inicialización y verificación de VOXMETRIK_V2'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Realiza una verificación completa'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='Obtiene información detallada'
    )

    args = parser.parse_args()

    if args.info:
        info_check()
        return True
    elif args.full:
        success = full_check()
    else:
        success = basic_check()

    # Resumen final
    logger.info("\n" + "="*60)
    if success:
        logger.info("✅ VERIFICACIÓN EXITOSA - Sistema listo para usar")
    else:
        logger.error("❌ VERIFICACIÓN FALLÓ - Revisar errores arriba")
    logger.info("="*60)

    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Verificación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        sys.exit(1)
