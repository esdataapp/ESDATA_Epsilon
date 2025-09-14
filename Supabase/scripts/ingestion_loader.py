"""Ingesta automática de CSVs y GeoJSON a Supabase/PostgreSQL.

Uso (PowerShell desde raíz del repo o carpeta Supabase):
    # Opción 1: Usar cadena completa
    $env:PGURL = "postgresql://usuario:pass@host.supabase.co:5432/postgres?sslmode=require"
    python Supabase/scripts/ingestion_loader.py --periodos Sep25

    # Opción 2: Usar partes
    $env:PG_HOST = "host.supabase.co"
    $env:PG_PASSWORD = "***"
    $env:PG_USER = "postgres"; $env:PG_DB = "postgres"; $env:PG_PORT = "5432"
    python Supabase/scripts/ingestion_loader.py --periodos Sep25

    Agregar --dry-run para simular sin cargar.

Flujo:
 - Detecta archivos finales en N5_Resultados/Nivel_1/CSV
 - Ordena carga: final_num -> final_amenidades -> final_marketing -> metodos_representativos -> resumen_colonia (si existe)
 - Inserta usando COPY para velocidad.
 - Crea geom si faltan puntos.
 - Loguea métricas por tabla.

NOTA: Este script no sube artefactos exclusivos del dashboard.
"""
from __future__ import annotations
import os
import sys
import json
import time
import glob
import argparse
import psycopg2
from contextlib import contextmanager
from typing import List, Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_BASE = os.path.join(BASE_DIR, 'N5_Resultados', 'Nivel_1', 'CSV')
PERIODOS_TARGET = None  # Se puede sobre-escribir vía argumento --periodos

TABLE_MAPPING = {
    '0.Final_Num': 'final_num',
    '0.Final_Ame': 'final_amenidades',
    '0.Final_MKT': 'final_marketing',
    'metodos_representativos': 'metodos_representativos'
}

REQUIRED_COLS = {
    'final_num': ['id', 'precio', 'area_m2', 'ciudad', 'colonia', 'periodo'],
    'final_amenidades': ['id', 'periodo'],
    'final_marketing': ['id', 'periodo'],
}

@contextmanager
def pg_conn():
    """Devuelve conexión usando PGURL si existe, si no construye desde partes."""
    pgurl = os.getenv('PGURL')
    if pgurl:
        conn = psycopg2.connect(pgurl)
    else:
        cfg = {
            'host': os.getenv('PG_HOST','localhost'),
            'port': int(os.getenv('PG_PORT','5432')),
            'dbname': os.getenv('PG_DB','esdata'),
            'user': os.getenv('PG_USER','postgres'),
            'password': os.getenv('PG_PASSWORD','postgres')
        }
        conn = psycopg2.connect(**cfg)
    try:
        yield conn
    finally:
        conn.close()


def discover_csvs(periodos: List[str] | None = None) -> List[Dict[str,str]]:
    pattern = os.path.join(CSV_BASE, '*.csv')
    files = glob.glob(pattern)
    artifacts = []
    for f in files:
        name = os.path.basename(f)
        # Detect periodo como último token antes de .csv separado por '_' (heurística)
        parts = name.split('_')
        if len(parts) >= 2:
            periodo_candidate = parts[-1].replace('.csv','')
        else:
            periodo_candidate = 'UNK'
        if periodos and periodo_candidate not in periodos:
            continue
        for prefix, table in TABLE_MAPPING.items():
            if name.startswith(prefix):
                artifacts.append({'file': f, 'table': table, 'periodo': periodo_candidate, 'name': name})
                break
    return artifacts


def copy_csv(conn, table: str, file_path: str):
    with conn.cursor() as cur, open(file_path, 'r', encoding='utf-8') as fh:
        cur.copy_expert(sql=f"COPY {table} FROM STDIN WITH CSV HEADER", file=fh)
    conn.commit()


def ensure_geom(conn):
    sql = """
    UPDATE final_num
    SET geom = ST_SetSRID(ST_MakePoint(longitud, latitud),4326)
    WHERE geom IS NULL AND longitud IS NOT NULL AND latitud IS NOT NULL;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def validate_columns(file_path: str, required: List[str]) -> bool:
    import csv
    with open(file_path, 'r', encoding='utf-8') as fh:
        reader = csv.reader(fh)
        header = next(reader)
    missing = [c for c in required if c not in header]
    if missing:
        print(f"[WARN] {os.path.basename(file_path)} faltan columnas requeridas: {missing}")
        return False
    return True


def ingest(periodos: List[str] | None = None, dry_run: bool = False):
    artifacts = discover_csvs(periodos)
    if not artifacts:
        print('[INFO] No se encontraron CSVs para ingesta')
        return

    # Orden de prioridad
    order = ['final_num', 'final_amenidades', 'final_marketing', 'metodos_representativos']
    artifacts.sort(key=lambda x: order.index(x['table']) if x['table'] in order else 999)

    summary = []
    with pg_conn() as conn:
        for art in artifacts:
            table = art['table']
            file_path = art['file']
            name = art['name']
            print(f"[INFO] Iniciando carga {name} -> {table}")
            t0 = time.time()
            if table in REQUIRED_COLS and not validate_columns(file_path, REQUIRED_COLS[table]):
                print(f"[SKIP] Columnas insuficientes para {name}")
                continue
            try:
                if dry_run:
                    print(f"[DRY-RUN] Simulando COPY {file_path} -> {table}")
                else:
                    copy_csv(conn, table, file_path)
                elapsed = time.time() - t0
                with conn.cursor() as cur:
                    cur.execute(f'SELECT COUNT(*) FROM {table};')
                    total = cur.fetchone()[0]
                print(f"[OK] {name} -> {table} ({elapsed:.2f}s) total filas tabla: {total}")
                summary.append({
                    'archivo': name,
                    'tabla': table,
                    'periodo': art['periodo'],
                    'tiempo_seg': round(elapsed,2),
                    'total_tabla_post': total
                })
            except Exception as e:
                conn.rollback()
                print(f"[ERROR] Fallo carga {name}: {e}")
        # Post procesos
        if not dry_run:
            try:
                ensure_geom(conn)
                print('[OK] Geometrías actualizadas')
            except Exception as e:
                print(f'[WARN] No se pudo actualizar geom: {e}')

    if summary:
        print('\n=== RESUMEN CARGA ===')
        for r in summary:
            print(json.dumps(r, ensure_ascii=False))
        # Detección simple de duplicados id (si tabla principal)
        if not dry_run:
            with pg_conn() as conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT periodo, COUNT(*) total, COUNT(DISTINCT id) distinct_ids FROM final_num GROUP BY periodo;")
                        rows = cur.fetchall()
                        for periodo, total, distinct_ids in rows:
                            if total != distinct_ids:
                                print(f"[ALERT] Duplicados detectados en final_num periodo={periodo} (total={total} distinct={distinct_ids})")
                except Exception as e:
                    print(f"[WARN] No se pudo ejecutar verificación duplicados: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description='Ingesta CSV a Supabase/PostgreSQL')
    parser.add_argument('--periodos', nargs='*', help='Limitar a periodos específicos (ej: Sep25 May25)')
    parser.add_argument('--dry-run', action='store_true', help='Simular sin ejecutar COPY')
    return parser.parse_args()

if __name__ == '__main__':
    # Carga .env si existe en BASE_DIR/Supabase o raíz
    try:
        from dotenv import load_dotenv
        # Buscar .env en raíz del repo
        root_env = os.path.join(BASE_DIR, '.env')
        supabase_env = os.path.join(BASE_DIR, 'Supabase', '.env')
        for candidate in (root_env, supabase_env):
            if os.path.isfile(candidate):
                load_dotenv(candidate)
    except Exception:
        pass
    args = parse_args()
    ingest(periodos=args.periodos, dry_run=args.dry_run)
