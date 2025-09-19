"""Paso 1: Consolidar y Adecuar Variables
- Lee todos los CSV de Base_de_Datos + Esperando periodo anterior
- Normaliza columnas segun 'Listas de Variables CSV.txt'
- Estandariza valores usando 'Lista de Variables Orquestacion.csv'
- Genera ID único compuesto: tipo-precio-area_rec-banos-estac_anunc-lng-lat (Ciudad-Colonia se agregan en paso 2)
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
    'id','PaginaWeb','Ciudad','Colonia','Fecha_Scrap','tipo_propiedad','area_m2','recamaras','estacionamientos','operacion',
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

# Variables globales para mapeos de estandarización
_STANDARDIZATION_MAPS = {}
_MAPS_LOADED = False

def load_standardization_maps():
    """Carga los mapeos de estandarización desde Lista de Variables Orquestacion.csv"""
    global _STANDARDIZATION_MAPS, _MAPS_LOADED
    
    if _MAPS_LOADED:
        return _STANDARDIZATION_MAPS
    
    csv_path = path_base('docs', 'Lista de Varibales Orquestacion.csv')
    if not os.path.exists(csv_path):
        log.warning(f'No se encontró archivo de estandarización: {csv_path}')
        return {}
    
    try:
        df = pd.read_csv(csv_path, header=None, names=['original', 'abrev'])
        
        maps = {
            'PaginaWeb': {},
            'Ciudad': {},
            'operacion': {},
            'tipo_propiedad': {},  # ProductoPaginaWeb
            'Mes': {},
            'Año': {}
        }
        
        current_section = None
        
        for idx, row in df.iterrows():
            original = str(row['original']).strip()
            abrev = str(row['abrev']).strip()
            
            # Detectar inicio de sección
            if original.startswith('1. PaginaWeb'):
                current_section = 'PaginaWeb'
                continue
            elif original.startswith('2. Ciudad'):
                current_section = 'Ciudad'
                continue
            elif original.startswith('3. Operacion'):
                current_section = 'operacion'
                continue
            elif original.startswith('4. ProductoPaginaWeb'):
                current_section = 'tipo_propiedad'
                continue
            elif original.startswith('5. Meses'):
                current_section = 'Mes'
                continue
            elif original.startswith('6. Año'):
                current_section = 'Año'
                continue
            
            # Saltar filas vacías o de encabezado
            if (pd.isna(row['original']) or pd.isna(row['abrev']) or 
                original == '' or abrev == '' or abrev == 'Name'):
                continue
            
            # Agregar mapeo a la sección actual
            if current_section and current_section in maps:
                # Mapear tanto el original como versiones en minúsculas/mayúsculas
                maps[current_section][original] = abrev
                maps[current_section][original.lower()] = abrev
                maps[current_section][original.upper()] = abrev
                maps[current_section][original.title()] = abrev
        
        _STANDARDIZATION_MAPS = maps
        _MAPS_LOADED = True
        log.info(f'Mapeos de estandarización cargados: {sum(len(m) for m in maps.values())} entradas')
        
    except Exception as e:
        log.error(f'Error cargando mapeos de estandarización: {e}')
        return {}
    
    return _STANDARDIZATION_MAPS

def standardize_value(value, variable_name):
    """Estandariza un valor usando los mapeos cargados"""
    if pd.isna(value) or value == '':
        return value
    
    maps = load_standardization_maps()
    if variable_name not in maps:
        return value
    
    str_value = str(value).strip()
    
    # Buscar en mapeos cargados primero
    if str_value in maps[variable_name]:
        return maps[variable_name][str_value]
    
    # Mapeos adicionales para tipo_propiedad que no están en el CSV
    if variable_name == 'tipo_propiedad':
        tipo_lower = str_value.lower().strip()
        
        # Mapeos adicionales comunes
        additional_mappings = {
            'lote': 'Terr',
            'lotes': 'Terr', 
            'terreno': 'Terr',
            'terrenos': 'Terr',
            'casa': 'Cas',
            'casas': 'Cas',
            'departamento': 'Dep',
            'departamentos': 'Dep',
            'depto': 'Dep',
            'deptos': 'Dep',
            'local comercial': 'LocC',
            'local': 'Loc',
            'locales': 'Loc',
            'oficina': 'Ofc',
            'oficinas': 'Ofc'
        }
        
        if tipo_lower in additional_mappings:
            return additional_mappings[tipo_lower]
    
    return str_value

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
    'PaginaWeb','Ciudad','Colonia','tipo_propiedad','operacion','direccion','ubicacion_url','titulo','descripcion',
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
    """Genera ID con formato: tipo-precio-area_rec-banos-estac_anunc-lng-lat
    Ciudad y Colonia se agregarán en el paso 2"""
    
    def format_text_field(val, min_chars=3, max_chars=4):
        """Formatea campos de texto"""
        if pd.isna(val) or val is None:
            return "0" * min_chars
        s = str(val).strip()
        if s == '' or s.lower() == 'desconocido':
            return "0" * min_chars
        # Solo caracteres alfanuméricos
        s = ''.join(c for c in s if c.isalnum())
        if not s:
            return "0" * min_chars
        # Ajustar longitud
        if len(s) < min_chars:
            return s.ljust(min_chars, '0')
        elif len(s) > max_chars:
            return s[:max_chars]
        return s
    
    def format_precio_millones(val):
        """Formatea precio en millones con M (3-4 números + M)"""
        if pd.isna(val) or val is None:
            return "000M"
        try:
            precio_num = float(val)
            millones = precio_num / 1000000
            if millones < 1:
                # Menos de 1 millón, usar formato sin M
                if precio_num < 1000:
                    return f"{int(precio_num):03d}"[:3]
                else:
                    # En miles
                    miles = int(precio_num / 1000)
                    return f"{miles:03d}"[:3] + "K"
            else:
                # En millones
                millones_int = int(millones)
                if millones_int < 1000:
                    return f"{millones_int:03d}M"
                else:
                    return f"{millones_int:04d}"[:3] + "M"
        except:
            return "000M"
    
    def format_area(val):
        """Formatea área (3-4 números)"""
        if pd.isna(val) or val is None:
            return "000"
        try:
            area_int = int(float(val))
            if area_int < 1000:
                return f"{area_int:03d}"
            else:
                return f"{area_int:04d}"[:4]
        except:
            return "000"
    
    def format_small_number(val, digits=2):
        """Formatea números pequeños (recamaras, baños, estacionamientos)"""
        if pd.isna(val) or val is None:
            return "0" * digits
        try:
            num = int(float(val))
            return f"{num:0{digits}d}"[:digits]
        except:
            return "0" * digits
    
    def format_anunciante(val):
        """Formatea anunciante (4-5 letras)"""
        if pd.isna(val) or val is None:
            return "0000"
        s = str(val).strip()
        if s == '' or s.lower() == 'desconocido':
            return "0000"
        # Solo caracteres alfanuméricos
        s = ''.join(c for c in s if c.isalnum())
        if not s:
            return "0000"
        # Ajustar longitud (4-5 caracteres)
        if len(s) < 4:
            return s.ljust(4, '0')
        elif len(s) > 5:
            return s[:5]
        return s
    
    def format_coordinate(val):
        """Formatea coordenadas (5 números)"""
        if pd.isna(val) or val is None:
            return "00000"
        try:
            # Convertir a entero multiplicado por 1000 para mantener 3 decimales
            coord_int = int(abs(float(val)) * 1000)
            return f"{coord_int:05d}"[:5]
        except:
            return "00000"
    
    # Extraer y formatear valores (sin ciudad y colonia)
    tipo = format_text_field(row.get('tipo_propiedad'), 3, 4)
    precio = format_precio_millones(row.get('precio'))
    area = format_area(row.get('area_m2'))
    recamaras = format_small_number(row.get('recamaras'), 2)
    banos = format_small_number(row.get('Banos_totales') or row.get('banos_icon'), 2)
    estacionamientos = format_small_number(row.get('estacionamientos'), 2)
    anunciante = format_anunciante(row.get('anunciante') or row.get('codigo_anunciante'))
    longitud = format_coordinate(row.get('longitud'))
    latitud = format_coordinate(row.get('latitud'))
    
    # Construir ID parcial: tipo-precio-area_rec-banos-estac_anunc-lng-lat
    return f"{tipo}-{precio}-{area}_{recamaras}-{banos}-{estacionamientos}_{anunciante}-{longitud}-{latitud}"

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
    
    # Eliminar columnas duplicadas e innecesarias (las que mencionas de columnas 33-41)
    # PERO manteniendo las columnas esenciales del pipeline
    unwanted_columns = [
        'Tipo de Propiedad', 'Superficie', 'Estacionamiento', 
        'Operación', 'CaracterÃ­sticas', 'generales', 'latitude', 'longitude',
        'Características', 'Superficie ', 'Estacionamiento ',
        'Operación ', 'Tipo de Propiedad ', 'latitude ', 'longitude '
    ]
    
    # Columnas esenciales que NUNCA deben eliminarse
    essential_columns = [
        'id', 'precio', 'recamaras', 'area_m2', 'tipo_propiedad', 'operacion',
        'Ciudad', 'PaginaWeb', 'Colonia', 'longitud', 'latitud'
    ]
    
    columns_to_drop = []
    for col in df.columns:
        # NO eliminar columnas esenciales
        if col in essential_columns:
            continue
        
        # Eliminar columnas duplicadas exactas
        if col in unwanted_columns:
            columns_to_drop.append(col)
        # Eliminar columnas que son variantes con espacios o caracteres especiales  
        elif any(col.strip().lower() == unwanted.strip().lower() for unwanted in unwanted_columns):
            columns_to_drop.append(col)
        # Eliminar duplicados específicos pero solo si tienen mayúsculas/espacios
        elif col in ['Precio', 'Recamaras'] and col != col.lower():
            columns_to_drop.append(col)
    
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
        log.info(f'Eliminadas {len(columns_to_drop)} columnas duplicadas: {columns_to_drop}')
    
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
    
    # Estandarización usando Lista de Variables Orquestacion.csv
    log.info('Aplicando estandarización de variables...')
    
    # Contar cambios para estadísticas
    changes_stats = {}
    
    for col_name in ['PaginaWeb', 'Ciudad', 'tipo_propiedad', 'operacion']:
        if col_name in df.columns:
            before_values = df[col_name].copy()
            df[col_name] = df[col_name].apply(lambda v: standardize_value(v, col_name))
            changes = sum(before_values != df[col_name])
            changes_stats[col_name] = changes
    
    # Estandarización adicional para fechas si existen columnas de mes/año
    if 'Mes' in df.columns:
        before_mes = df['Mes'].copy()
        df['Mes'] = df['Mes'].apply(lambda v: standardize_value(v, 'Mes'))
        changes_stats['Mes'] = sum(before_mes != df['Mes'])
        
    if 'Año' in df.columns or 'Year' in df.columns:
        año_col = 'Año' if 'Año' in df.columns else 'Year'
        before_año = df[año_col].copy()
        df[año_col] = df[año_col].apply(lambda v: standardize_value(v, 'Año'))
        changes_stats[año_col] = sum(before_año != df[año_col])
    
    # Reportar estadísticas de estandarización
    total_changes = sum(changes_stats.values())
    if total_changes > 0:
        log.info(f'Estandarización completada: {total_changes} valores estandarizados')
        for col, changes in changes_stats.items():
            if changes > 0:
                log.info(f'  - {col}: {changes} valores estandarizados')
    else:
        log.info('No se realizaron cambios de estandarización')
    
    # Fecha
    df['Fecha_Scrap'] = df['Fecha_Scrap'].apply(_norm_fecha)
    # Numeros base
    for num_col in ['area_m2','precio','mantenimiento','area_total','area_cubierta']:
        if num_col in df.columns:
            df[num_col]=df[num_col].apply(_clean_number)
        else:
            log.warning(f'Columna numérica {num_col} no encontrada en el DataFrame')
    # Redondeo 2 decimales para superficies y precio/mantenimiento
    for rcol in ['area_m2','precio','mantenimiento','area_total','area_cubierta']:
        if rcol in df.columns:
            # Validar que la columna sea numérica antes de redondear
            if pd.api.types.is_numeric_dtype(df[rcol]):
                df[rcol]=df[rcol].round(2)
            else:
                log.warning(f'Columna {rcol} no es numérica, saltando redondeo')
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
    
    # Limpieza final: mantener solo columnas necesarias
    final_columns = []
    for col in df.columns:
        # Mantener columnas de VAR_FILE_ORDER
        if col in VAR_FILE_ORDER:
            final_columns.append(col)
        # Mantener columnas de coordenadas
        elif col in ['longitud', 'latitud', 'Banos_totales', 'PxM2']:
            final_columns.append(col)
        # Mantener flags de missing/zero
        elif col.startswith('missing_') or col.startswith('zero_'):
            final_columns.append(col)
        # Mantener columnas del origen
        elif col.startswith('__'):
            final_columns.append(col)
    
    # Filtrar solo las columnas necesarias
    available_columns = [col for col in final_columns if col in df.columns]
    df = df[available_columns].copy()
    
    log.info(f'DataFrame final con {len(df.columns)} columnas: {len(available_columns)} columnas mantenidas')
    
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
