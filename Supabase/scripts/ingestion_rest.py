"""Ingesta de CSV a Supabase usando la REST Data API (postgrest) cuando no es posible
conectar vía psycopg2 (limitaciones IPv4/IPv6 en plan gratuito).

Requisitos:
  - SUPABASE_URL  (ej: https://twyyefzygxdljniyxdjv.supabase.co)
  - SUPABASE_SERVICE_KEY (service_role key, mantener privada)

Uso:
  (PowerShell)
    $env:SUPABASE_URL = "https://twyyefzygxdljniyxdjv.supabase.co"
    $env:SUPABASE_SERVICE_KEY = "eyJ... (service role)"
    python Supabase/scripts/ingestion_rest.py --periodos Sep25 --dry-run
    python Supabase/scripts/ingestion_rest.py --periodos Sep25

Notas:
  - Inserta en lotes (chunk) para reducir overhead HTTP.
  - Si una tabla ya tiene filas del periodo, se puede activar --replace-periodo para
    borrar antes (DELETE where periodo=...).
  - Usa el mismo mapeo que ingestion_loader.py: final_num, final_amenidades, final_marketing.
"""
from __future__ import annotations
import os
import csv
import json
import time
import glob
import argparse
import requests
from typing import List, Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_BASE = os.path.join(BASE_DIR, 'N5_Resultados', 'Nivel_1', 'CSV')
TABLE_MAPPING = {
    '0.Final_Num': 'final_num',
    '0.Final_Ame': 'final_amenidades',
    '0.Final_MKT': 'final_marketing',
}

REQUIRED_COLS = {
    'final_num': ['id','precio','area_m2','ciudad','colonia','periodo'],
    'final_amenidades': ['id','periodo'],
    'final_marketing': ['id','periodo'],
}

CHUNK_SIZE = 500  # Ajustable


def discover_csvs(periodos: List[str] | None = None) -> List[Dict[str,str]]:
    pattern = os.path.join(CSV_BASE, '*.csv')
    files = glob.glob(pattern)
    artifacts = []
    for f in files:
        name = os.path.basename(f)
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


def load_rows(file_path: str) -> List[Dict[str,str]]:
    with open(file_path, 'r', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def validate_columns(file_path: str, table: str) -> bool:
    required = REQUIRED_COLS.get(table)
    if not required:
        return True
    with open(file_path, 'r', encoding='utf-8') as fh:
        reader = csv.reader(fh)
        header = next(reader)
    missing = [c for c in required if c not in header]
    if missing:
        print(f"[WARN] {file_path} faltan columnas: {missing}")
        return False
    return True


def rest_insert(table: str, rows: List[Dict[str,str]], url: str, key: str, dry_run: bool):
    endpoint = f"{url}/rest/v1/{table}"
    headers = {
        'apikey': key,
        'Authorization': f"Bearer {key}",
        'Content-Type': 'application/json'
    }
    total = 0
    for i in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[i:i+CHUNK_SIZE]
        if dry_run:
            print(f"[DRY-RUN] {table} inserción chunk {i//CHUNK_SIZE+1} ({len(chunk)} filas)")
            continue
        r = requests.post(endpoint, headers=headers, data=json.dumps(chunk), params={'return':'minimal'} )
        if r.status_code not in (200,201,204):
            print(f"[ERROR] POST {table} status={r.status_code} body={r.text[:300]}")
            raise SystemExit(1)
        total += len(chunk)
    if not dry_run:
        print(f"[OK] Insertadas {total} filas en {table}")


def delete_period(table: str, periodo: str, url: str, key: str):
    endpoint = f"{url}/rest/v1/{table}";
    headers = {
        'apikey': key,
        'Authorization': f"Bearer {key}",
        'Content-Type': 'application/json'
    }
    r = requests.delete(endpoint, headers=headers, params={'periodo':'eq.'+periodo})
    if r.status_code not in (200,204):
        print(f"[WARN] No se pudo borrar periodo={periodo} en {table}: {r.status_code} {r.text[:120]}")


def count_table(table: str, url: str, key: str) -> int:
    endpoint = f"{url}/rest/v1/{table}";
    headers = {
        'apikey': key,
        'Authorization': f"Bearer {key}",
        'Range': '0-0',
        'Prefer': 'count=exact'
    }
    r = requests.get(endpoint, headers=headers)
    if 'content-range' in r.headers:
        try:
            total = r.headers['content-range'].split('/')[-1]
            return int(total)
        except Exception:
            return -1
    return -1


def ingest(periodos: List[str] | None, dry_run: bool, replace: bool):
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    if not (supabase_url and supabase_key):
        print('[ERROR] Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY')
        raise SystemExit(1)

    artifacts = discover_csvs(periodos)
    if not artifacts:
        print('[INFO] No se encontraron CSVs para ingesta')
        return
    # Orden consistente con script psycopg2
    order = ['final_num','final_amenidades','final_marketing']
    artifacts.sort(key=lambda x: order.index(x['table']) if x['table'] in order else 999)

    for art in artifacts:
        table = art['table']
        periodo = art['periodo']
        file_path = art['file']
        print(f"[INFO] Procesando {art['name']} -> {table} periodo={periodo}")
        if not validate_columns(file_path, table):
            print('[SKIP] Columnas insuficientes')
            continue
        rows = load_rows(file_path)
        if replace and not dry_run:
            delete_period(table, periodo, supabase_url, supabase_key)
        rest_insert(table, rows, supabase_url, supabase_key, dry_run)
        if not dry_run:
            total = count_table(table, supabase_url, supabase_key)
            print(f"[TOTAL] {table} filas ahora: {total}")


def parse_args():
    p = argparse.ArgumentParser(description='Ingesta REST a Supabase')
    p.add_argument('--periodos', nargs='*', help='Limitar periodos (ej: Sep25 May25)')
    p.add_argument('--dry-run', action='store_true', help='Simular')
    p.add_argument('--replace-periodo', action='store_true', help='Borrar filas del periodo antes de insertar')
    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()
    ingest(args.periodos, args.dry_run, args.replace_periodo)
