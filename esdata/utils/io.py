import os
import pandas as pd
from .logging_setup import get_logger

log = get_logger('io')

# Encoding principal y fallback para archivos que vienen en ISO-8859-1/Windows-1252
ENCODING = 'utf-8-sig'
FALLBACK_ENCODINGS = ['latin-1', 'cp1252']

def read_csv(path: str) -> pd.DataFrame:
    """Lee un CSV intentando primero UTF-8 y aplicando codificaciones fallback si falla.
    Se limita a UnicodeDecodeError para no ocultar otros problemas.
    """
    log.info(f"Leyendo CSV: {path}")
    try:
        return pd.read_csv(path, encoding=ENCODING)
    except UnicodeDecodeError as e:
        for fb in FALLBACK_ENCODINGS:
            try:
                log.warning(f"Reintentando lectura con encoding fallback '{fb}' por error: {e}")
                return pd.read_csv(path, encoding=fb)
            except UnicodeDecodeError:
                continue
        # Último recurso: intentar lectura con errores reemplazados para no detener pipeline
    log.error(f"Fallo lectura en todos los encodings ({[ENCODING]+FALLBACK_ENCODINGS}). Se intenta rescatar con 'latin-1' y on_bad_lines='skip'.")
    return pd.read_csv(path, encoding='latin-1', on_bad_lines='skip')

def write_csv(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log.info(f"Escribiendo CSV: {path} ({len(df)} filas / {len(df.columns)} cols)")
    df.to_csv(path, index=False, encoding=ENCODING)
