"""Prueba rápida de conexión a Supabase/PostgreSQL usando PGURL del entorno.

Uso:
  (PowerShell)
    python Supabase/scripts/test_connection.py

Requisitos:
  - Variable de entorno PGURL (o PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD)
  - psycopg2-binary instalado
"""
import os
import socket
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import psycopg2


def build_url_from_parts():
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT", "5432")
    db = os.getenv("PG_DB", "postgres")
    user = os.getenv("PG_USER", "postgres")
    pwd = os.getenv("PG_PASSWORD")
    if not (host and pwd):
        raise RuntimeError("Faltan PG_HOST o PG_PASSWORD para construir la URL")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}?sslmode=require"


def dns_check(host: str):
    try:
        ip = socket.gethostbyname(host)
        print(f"[DNS] {host} -> {ip}")
        return True
    except Exception as e:
        print(f"[DNS-ERROR] {host} no resolvió: {e}")
        return False


def build_pooler_url(original_url: str) -> str:
    """Construye una URL usando el Session Pooler si el host directo no resuelve.
    Requiere extraer el project ref (segmento entre db. y .supabase.co)
    Región asumida: us-east-2 (ajustar con SUPABASE_POOLER_REGION si cambia)
    """
    region = os.getenv('SUPABASE_POOLER_REGION', 'us-east-2')
    parsed = urlparse(original_url)
    host = parsed.hostname or ''
    project_ref = ''
    if host.startswith('db.') and '.supabase.co' in host:
        project_ref = host.split('db.')[1].split('.supabase.co')[0]
    if not project_ref:
        return ''
    pooler_host = f"aws-1-{region}.pooler.supabase.com"
    q = parse_qs(parsed.query)
    q['sslmode'] = ['require']
    q['options'] = [f"project={project_ref}"]
    new_query = urlencode({k:v[0] for k,v in q.items()})
    rebuilt = urlunparse((parsed.scheme, f"{pooler_host}:{parsed.port or 5432}", parsed.path, '', new_query, ''))
    return rebuilt


def main():
    url = os.getenv("PGURL")
    if not url:
        url = build_url_from_parts()
    masked = f"{url.split('://')[0]}://***:***@{url.split('@')[1]}"
    print(f"Usando URL (ocultando password): {masked}")

    # DNS diagnostic
    try:
        host = urlparse(url).hostname
    except Exception:
        host = None
    if host:
        ok = dns_check(host)
        if not ok and host.startswith('db.'):
            alt = build_pooler_url(url)
            if alt:
                print('[INFO] Intentando fallback a Session Pooler:', alt.replace(url.split('://')[0]+':','postgresql:').replace('//postgresql','//'))
                try:
                    conn = psycopg2.connect(alt)
                    with conn.cursor() as cur:
                        cur.execute('SELECT 1;')
                        cur.fetchone()
                    conn.close()
                    print('[OK] Fallback pooler exitoso. Puedes exportar esta URL para la ingesta:')
                    print('    $env:PGURL = "' + alt + '"')
                    return
                except Exception as e:
                    print('[FALLBACK-ERROR] Pooler también falló:', e)
    try:
        conn = psycopg2.connect(url)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.execute("SELECT current_database(), current_user;")
            db_user = cur.fetchone()
        conn.close()
        print("[OK] Conexión exitosa")
        print("Version:", version)
        print("DB/User:", db_user)
    except Exception as e:
        print("[ERROR]", e)
        print("Sugerencias:")
        print("  1) Verifica que el host exista: nslookup", host or '(sin host)')
        print("  2) Revisa en el panel de Supabase el Connection String Direct Connection exacto")
        print("  3) Si firewall corporativo, prueba desde otra red o utiliza el pooler (ver docs)")
        print("  4) Si usas VPN, desactívala temporalmente")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
