"""Paso 1: Consolidar y Adecuar Variables
- Lee todos los CSV de Base_de_Datos + Esperando periodo anterior
- Normaliza columnas segun 'Listas de Variables CSV.txt'
- Genera ID único compuesto: <Periodo><Ciudad><Operacion><Tipo><hash>
- Calcula Longitud/Latitud desde ubicacion_url
- Crea Banos_totales
- NO elimina propiedades
"""
from __future__ import annotations
import os, re, hashlib, glob, sys
import pandas as pd
from datetime import datetime
from esdata.utils.paths import path_input_base, ensure_dir, path_consolidados, obtener_periodo_previo, path_base
from esdata.utils.paths import path_esperando as _path_esperando  # para no crear si no existe manualmente
from esdata.utils.io import read_csv, write_csv
from esdata.utils.logging_setup import get_logger

log = get_logger('step1')

VAR_FILE_ORDER = [
    'id','PaginaWeb','Ciudad','Fecha_Scrap','tipo_propiedad','area_m2','recamaras','estacionamientos','operacion',
    'precio','mantenimiento','direccion','ubicacion_url','titulo','descripcion','anunciante','codigo_anunciante',
    'codigo_inmuebles24','tiempo_publicacion','area_total','area_cubierta','banos_icon','estacionamientos_icon',
    'recamaras_icon','medio_banos_icon','antiguedad_icon','Caracteristicas_generales','Servicios','Amenidades','Exteriores'
]

# Mapeo de nombres de columnas para normalizar inconsistencias
COLUMN_NAME_MAPPING = {
    'Características generales': 'Caracteristicas_generales',
    'características generales': 'Caracteristicas_generales',
    'CARACTERÍSTICAS GENERALES': 'Caracteristicas_generales',
    'caracteristicas generales': 'Caracteristicas_generales'
}

RE_COORD = re.compile(r'center=([+-]?\d+\.?\d*),([+-]?\d+\.?\d*)')

ABREV_TIPO = {'Departamento':'Dep','DEPARTAMENTO':'Dep','Dep':'Dep','Casa':'Cas','CASA':'Cas','Oficina':'Ofc','Ofic':'Ofc'}
ABREV_OPER = {'venta':'Ven','Venta':'Ven','VEN':'Ven','renta':'Ren','Renta':'Ren'}
ABREV_CIUD = {'Guadalajara':'Gdl','GDL':'Gdl','Zapopan':'Zap','ZAP':'Zap','Tlaquepaque':'Tlaq'}

PERIODO_ACTUAL = datetime.now().strftime('%b%y')  # ej. Sep25 (default cuando no se pasa argumento)
# Permite override cuando se ejecuta con periodo específico
_PERIODO_OVERRIDE: str|None = None

FLOAT_CLEAN_RE = re.compile(r'[^\d.,]')
NUM_IN_TEXT_RE = re.compile(r'(\d+[\d.,]*)')
BANOS_RE = re.compile(r'(\d+(?:\.\d+)?)\s*ba', re.IGNORECASE)
REC_RE = re.compile(r'(\d+)\s*rec', re.IGNORECASE)
ESTAC_RE = re.compile(r'(\d+)\s*estac', re.IGNORECASE)
MEDIO_BANO_RE = re.compile(r'(\d+)\s*medio', re.IGNORECASE)
TIEMPO_DIAS_RE = re.compile(r'hace\s+(\d+)\s*d[ií]as', re.IGNORECASE)
TIEMPO_MES_RE = re.compile(r'hace\s+(\d+)\s*mes', re.IGNORECASE)
ANTIG_ANIOS_RE = re.compile(r'(\d+)\s*año', re.IGNORECASE)

TEXT_COLUMNS_DESCONOCIDO = [
    'PaginaWeb','Ciudad','tipo_propiedad','operacion','direccion','ubicacion_url','titulo','descripcion',
    'anunciante','codigo_anunciante','codigo_inmuebles24','Caracteristicas_generales','Servicios','Amenidades','Exteriores'
]

NUMERIC_BASE_COLS = [
    'area_m2','precio','mantenimiento','recamaras','estacionamientos','area_total','area_cubierta',
    'banos_icon','medio_banos_icon','estacionamientos_icon','recamaras_icon','Banos_totales','tiempo_publicacion'
]

def _clean_number(val):
    if pd.isna(val):
        return None
    s = str(val)
    s = FLOAT_CLEAN_RE.sub('', s)
    if s.count(',')>0 and s.count('.')==0:
        s = s.replace(',','')
    else:
        s = s.replace(',','')
    try:
        return float(s) if s!='' else None
    except: return None

def _extract_coords(url):
    if not isinstance(url,str):
        return None, None
    m = RE_COORD.search(url)
    if not m: return None, None
    lat = round(float(m.group(1)),6)
    lon = round(float(m.group(2)),6)
    return lon, lat

def _norm_fecha(v):
    if pd.isna(v): return None
    s=str(v).strip()
    # Excel serial
    if s.isdigit() and len(s)<=5:
        try:
            base=datetime(1899,12,30)
            return (base+pd.to_timedelta(int(s),unit='D')).strftime('%d/%m/%Y')
        except: return None
    for fmt in ('%d/%m/%Y','%Y-%m-%d'):
        try: return datetime.strptime(s,fmt).strftime('%d/%m/%Y')
        except: pass
    return None

def _norm_simple(val, mapa):
    if pd.isna(val): return None
    v=str(val).strip()
    return mapa.get(v,v)

def _build_id(row):
    period = _PERIODO_OVERRIDE or PERIODO_ACTUAL
    # Manejo seguro de valores nulos para evitar IDs inconsistentes
    ciudad = str(row.get('Ciudad') or 'Unknown').strip()
    operacion = str(row.get('operacion') or 'Unknown').strip()
    tipo = str(row.get('tipo_propiedad') or 'Unknown').strip()
    titulo = str(row.get('titulo') or 'Unknown').strip()
    precio = str(row.get('precio') or 'Unknown').strip()
    
    seed = f"{period}|{ciudad}|{operacion}|{tipo}|{titulo}|{precio}".lower()
    h = hashlib.sha1(seed.encode()).hexdigest()[:8]
    return f"{period}_{h}"

def cargar_csvs_fuente(periodo: str, include_waiting_prev: bool=True) -> pd.DataFrame:
    """Carga únicamente los CSV del periodo actual y opcionalmente los 'esperando' del periodo previo.
    Requisitos nuevos multi-periodo: evitar mezclar históricos para no inflar n_propiedades.
    """
    base_root = path_input_base()
    period_dir = os.path.join(base_root, periodo)
    if not os.path.isdir(period_dir):
        raise FileNotFoundError(f"No existe carpeta de periodo: {period_dir}")
    patrones = glob.glob(os.path.join(period_dir,'*.csv'))
    frames: list[pd.DataFrame] = []
    for p in patrones:
        try:
            df = read_csv(p)
            df['__origen_archivo'] = os.path.basename(p)
            df['__fuente_periodo'] = periodo
            frames.append(df)
        except Exception as e:
            log.warning(f"No se pudo leer {p}: {e}")
    if include_waiting_prev:
        prev = obtener_periodo_previo(periodo)
        esperando_dir = os.path.join(path_base('Datos_Filtrados','Esperando', prev))
        if os.path.isdir(esperando_dir):
            wait_csvs = glob.glob(os.path.join(esperando_dir,'*.csv'))
            for wp in wait_csvs:
                try:
                    wdf = read_csv(wp)
                    wdf['__origen_archivo'] = os.path.basename(wp)
                    wdf['__fuente_periodo'] = prev
                    wdf['__flag_esperando_prev'] = 1
                    frames.append(wdf)
                except Exception as e:
                    log.warning(f"No se pudo leer esperando {wp}: {e}")
        else:
            log.info(f"No existe carpeta esperando del periodo previo ({prev}), se omite")
    if not frames:
        raise FileNotFoundError('No se encontraron CSV en carpeta del periodo actual')
    return pd.concat(frames, ignore_index=True)

def _parse_icon_numeric(series: pd.Series, pattern: re.Pattern, decimal: bool=False):
    out=[]
    for v in series:
        if pd.isna(v):
            out.append(None); continue
        s=str(v)
        m=pattern.search(s)
        if not m:
            out.append(None)
        else:
            try:
                val = float(m.group(1)) if decimal else int(m.group(1))
                out.append(val)
            except:
                out.append(None)
    return out

def _parse_tiempo_publicacion(val):
    if pd.isna(val):
        return None
    s=str(val).lower()
    if 'más de un año' in s or 'mas de un año' in s or 'mas de 1 año' in s:
        return 366
    if 'hoy' in s:
        return 0
    if 'ayer' in s:
        return 1
    md = TIEMPO_DIAS_RE.search(s)
    if md:
        try: return int(md.group(1))
        except: return None
    mm = TIEMPO_MES_RE.search(s)
    if mm:
        try:
            return int(mm.group(1))*30
        except: return None
    return None

def _parse_antiguedad(val):
    if pd.isna(val): return None
    s=str(val).lower()
    if 'estrenar' in s:
        return 0
    ma = ANTIG_ANIOS_RE.search(s)
    if ma:
        try: return int(ma.group(1))
        except: return None
    # mantener texto si es 'en construcción' etc.
    if any(k in s for k in ['construcción','preventa','remodelar']):
        return s
    return None

def _fill_desconocido(df: pd.DataFrame):
    for col in TEXT_COLUMNS_DESCONOCIDO:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: 'Desconocido' if (pd.isna(x) or str(x).strip()=='' ) else str(x).strip())
    return df

def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    # Eliminar columnas basura Unnamed
    drop_cols=[c for c in df.columns if c.startswith('Unnamed')]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    # Normalizar variantes de 'Fecha_Scrap' antes de crear/asegurar columnas
    # Detecta columnas como 'fecha_scrap', 'FechaScrap', 'Fecha scrap', 'fechaScrape', etc.
    variantes_fecha = []
    for c in list(df.columns):
        norm = re.sub(r'[^a-z]', '', c.lower())
        if norm == 'fechascrap' and c != 'Fecha_Scrap':
            variantes_fecha.append(c)
    # Si existe más de una variante, escoger la de mayor número de valores no nulos
    if variantes_fecha:
        mejor = max(variantes_fecha, key=lambda x: df[x].notna().sum())
        # Renombrar la mejor a 'Fecha_Scrap' y descartar las otras fusionando datos donde mejor esté vacío
        if 'Fecha_Scrap' not in df.columns:
            df.rename(columns={mejor: 'Fecha_Scrap'}, inplace=True)
        else:
            # Ya existe 'Fecha_Scrap', combinar valores faltantes usando variante
            mask = (df['Fecha_Scrap'].isna() | (df['Fecha_Scrap'].astype(str).str.strip()=='')) & df[mejor].notna()
            df.loc[mask, 'Fecha_Scrap'] = df.loc[mask, mejor]
        for v in variantes_fecha:
            if v == mejor:
                continue
            mask2 = (df['Fecha_Scrap'].isna() | (df['Fecha_Scrap'].astype(str).str.strip()=='')) & df[v].notna()
            if mask2.any():
                df.loc[mask2, 'Fecha_Scrap'] = df.loc[mask2, v]
            # Eliminar columna redundante
            df.drop(columns=v, inplace=True)
    # Quitar espacios accidentales en nombre exacto
    if 'Fecha_Scrap ' in df.columns and 'Fecha_Scrap' not in df.columns:
        df.rename(columns={'Fecha_Scrap ': 'Fecha_Scrap'}, inplace=True)
    # Consolidar variantes de Caracteristicas_generales antes de asegurar columnas
    variantes_carac = [c for c in df.columns if c.lower().replace('í','i').replace('á','a').replace('é','e').replace('ó','o').replace('ú','u').replace('ñ','n').strip().replace(' ','_') in ['caracteristicas_generales','caracteristicas']]
    if len(variantes_carac)>1:
        # Escoger la que tenga más valores no nulos como principal
        mejor = max(variantes_carac, key=lambda c: df[c].notna().sum())
        contenido = df[mejor]
        for v in variantes_carac:
            if v==mejor: continue
            # Combinar donde principal está vacío y variante tiene dato
            mask = (contenido.isna() | (contenido.astype(str).str.strip()=='')) & df[v].notna()
            contenido.loc[mask]=df.loc[mask, v]
        # Eliminar todas y crear columna limpia única
        df = df.drop(columns=variantes_carac)
        df['Caracteristicas_generales']=contenido
    elif len(variantes_carac)==1 and 'Caracteristicas_generales' not in variantes_carac:
        # Renombrar a forma estándar
        df.rename(columns={variantes_carac[0]:'Caracteristicas_generales'}, inplace=True)
    # Unificar posibles variantes de coordenadas si vienen ya parseadas
    if 'Longitude' in df.columns and 'longitud' not in df.columns:
        df.rename(columns={'Longitude':'longitud'}, inplace=True)
    if 'Latitude' in df.columns and 'latitud' not in df.columns:
        df.rename(columns={'Latitude':'latitud'}, inplace=True)
    # Asegurar columnas del orden base
    for c in VAR_FILE_ORDER:
        if c not in df.columns:
            df[c]=None
    # Normalizaciones abreviaturas
    df['Ciudad'] = df['Ciudad'].apply(lambda v: _norm_simple(v,ABREV_CIUD))
    df['tipo_propiedad'] = df['tipo_propiedad'].apply(lambda v: _norm_simple(v,ABREV_TIPO))
    df['operacion'] = df['operacion'].apply(lambda v: _norm_simple(v,ABREV_OPER))
    # Fecha
    df['Fecha_Scrap'] = df['Fecha_Scrap'].apply(_norm_fecha)
    # Numeros base
    for num_col in ['area_m2','precio','mantenimiento','area_total','area_cubierta']:
        df[num_col]=df[num_col].apply(_clean_number)
    # Redondeo 2 decimales para superficies y precio/mantenimiento
    for rcol in ['area_m2','precio','mantenimiento','area_total','area_cubierta']:
        if rcol in df.columns:
            df[rcol]=df[rcol].round(2)
    # Parse iconos si vienen en texto
    if 'banos_icon' in df.columns:
        df['banos_icon'] = _parse_icon_numeric(df['banos_icon'], BANOS_RE, decimal=False)
    if 'estacionamientos_icon' in df.columns:
        df['estacionamientos_icon'] = _parse_icon_numeric(df['estacionamientos_icon'], ESTAC_RE)
    if 'recamaras_icon' in df.columns:
        df['recamaras_icon'] = _parse_icon_numeric(df['recamaras_icon'], REC_RE)
    if 'medio_banos_icon' in df.columns:
        df['medio_banos_icon'] = _parse_icon_numeric(df['medio_banos_icon'], MEDIO_BANO_RE)
    # Cast a numerico final
    for ic in ['recamaras','estacionamientos','recamaras_icon','estacionamientos_icon','medio_banos_icon']:
        if ic in df.columns:
            df[ic]=pd.to_numeric(df[ic], errors='coerce')
    if 'banos_icon' in df.columns:
        df['banos_icon']=pd.to_numeric(df['banos_icon'], errors='coerce')
    # Tiempo publicación y antigüedad
    if 'tiempo_publicacion' in df.columns:
        df['tiempo_publicacion'] = df['tiempo_publicacion'].apply(_parse_tiempo_publicacion)
    if 'antiguedad_icon' in df.columns:
        df['antiguedad_icon'] = df['antiguedad_icon'].apply(_parse_antiguedad)
    # Coordenadas desde URL si faltan
    coords = df['ubicacion_url'].apply(_extract_coords)
    if 'longitud' not in df.columns or df['longitud'].isna().all():
        df['longitud']=[c[0] for c in coords]
    else:
        # Completar vacíos
        lon_new=[c[0] for c in coords]
        df.loc[df['longitud'].isna(),'longitud']=pd.Series(lon_new)
    if 'latitud' not in df.columns or df['latitud'].isna().all():
        df['latitud']=[c[1] for c in coords]
    else:
        lat_new=[c[1] for c in coords]
        df.loc[df['latitud'].isna(),'latitud']=pd.Series(lat_new)
    # Baños totales
    if 'banos_icon' in df.columns and 'medio_banos_icon' in df.columns:
        df['Banos_totales']= (df['banos_icon'].fillna(0) + df['medio_banos_icon'].fillna(0)*0.5)
    else:
        df['Banos_totales']=None
    # Rellenar Desconocido en textos
    df = _fill_desconocido(df)
    # ID final
    df['id'] = df.apply(_build_id, axis=1)
    # Flags de faltantes y ceros (sin modificar valores)
    for col in NUMERIC_BASE_COLS:
        if col in df.columns:
            df[f'missing_{col}'] = df[col].isna().astype(int)
            # Flag específicos para distinguir cero explícito de faltante
            if col in ['precio','area_m2','mantenimiento','area_total','area_cubierta']:
                df[f'zero_{col}'] = ((df[col].fillna(0)==0) & (~df[f'missing_{col}'].astype(bool))).astype(int)
    return df

def run(output_period: str|None=None, include_waiting_prev: bool=True):
    global _PERIODO_OVERRIDE
    period = output_period or PERIODO_ACTUAL
    _PERIODO_OVERRIDE = period
    log.info(f'Iniciando Paso 1 Consolidacion Periodo {period} (include_waiting_prev={include_waiting_prev})')
    df = cargar_csvs_fuente(period, include_waiting_prev=include_waiting_prev)
    before=len(df)
    df = normalizar(df)
    after=len(df)
    log.info(f'Registros antes={before} despues={after} (no se eliminan)')
    out_dir = ensure_dir(os.path.join(path_consolidados(), f'{period}'))
    out_path = os.path.join(out_dir, f'1.Consolidado_Adecuado_{period}.csv')
    write_csv(df,out_path)
    log.info(f'Archivo generado {out_path}')
    return out_path

if __name__=='__main__':
    per = sys.argv[1] if len(sys.argv)>1 else None
    run(per)
