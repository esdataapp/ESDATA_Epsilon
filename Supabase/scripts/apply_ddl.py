"""Aplica en orden todos los archivos .sql en Supabase/ddl si la tabla base no existe.

Uso:
  python scripts/apply_ddl.py

Detecta existencia verificando la primera sentencia CREATE TABLE IF NOT EXISTS <tabla>.
"""
import os, re, psycopg2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DDL_DIR = os.path.join(BASE_DIR, 'ddl')

PGURL = os.getenv('PGURL')
if not PGURL:
    host = os.getenv('PG_HOST','localhost')
    port = os.getenv('PG_PORT','5432')
    db   = os.getenv('PG_DB','postgres')
    user = os.getenv('PG_USER','postgres')
    pwd  = os.getenv('PG_PASSWORD','postgres')
    PGURL = f"postgresql://{user}:{pwd}@{host}:{port}/{db}?sslmode=require"

create_regex = re.compile(r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)', re.IGNORECASE)

def main():
    ddl_files = sorted([f for f in os.listdir(DDL_DIR) if f.lower().endswith('.sql')])
    print('[INFO] Archivos DDL detectados:', ddl_files)
    conn = psycopg2.connect(PGURL)
    try:
        for fname in ddl_files:
            path = os.path.join(DDL_DIR, fname)
            with open(path, 'r', encoding='utf-8') as fh:
                sql = fh.read()
            # Extraer tablas
            tables = create_regex.findall(sql)
            to_execute = []
            with conn.cursor() as cur:
                for t in tables:
                    cur.execute("SELECT to_regclass(%s);", (t,))
                    exists = cur.fetchone()[0] is not None
                    if exists:
                        print(f"[SKIP] Tabla {t} ya existe (archivo {fname})")
                    else:
                        to_execute.append(t)
                if to_execute:
                    print(f"[APPLY] Ejecutando {fname} (creará: {', '.join(to_execute)})")
                    cur.execute(sql)
            conn.commit()
        print('[OK] DDL aplicado')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
