"""Ingesta automática de CSVs y GeoJSON a Supabase/PostgreSQL.

Uso:
 1. Configurar variables de entorno:
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
 2. Ajustar PERIODOS_TARGET si se desea limitar.
 3. Ejecutar: python ingestion_loader.py

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
import psycopg2
from contextlib import contextmanager
from typing import List, Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_BASE = os.path.join(BASE_DIR, 'N5_Resultados', 'Nivel_1', 'CSV')
PERIODOS_TARGET = None  # Ej: ['Sep25'] para limitar

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


def discover_csvs() -> List[Dict[str,str]]:
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
        if PERIODOS_TARGET and periodo_candidate not in PERIODOS_TARGET:
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


def ingest():
    artifacts = discover_csvs()
    if not artifacts:
        print('[INFO] No se encontraron CSVs para ingesta')
        return

    # Orden de prioridad
    order = ['final_num', 'final_amenidades', 'final_marketing', 'metodos_representativos']
    artifacts.sort(key=lambda x: order.index(x['table']) if x['table'] in order else 999)

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
                copy_csv(conn, table, file_path)
                elapsed = time.time() - t0
                with conn.cursor() as cur:
                    cur.execute(f'SELECT COUNT(*) FROM {table};')
                    total = cur.fetchone()[0]
                print(f"[OK] {name} -> {table} ({elapsed:.2f}s) total filas tabla: {total}")
            except Exception as e:
                conn.rollback()
                print(f"[ERROR] Fallo carga {name}: {e}")
        # Post procesos
        try:
            ensure_geom(conn)
            print('[OK] Geometrías actualizadas')
        except Exception as e:
            print(f'[WARN] No se pudo actualizar geom: {e}')

if __name__ == '__main__':
    ingest()
