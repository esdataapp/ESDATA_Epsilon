"""Paso 2: Procesamiento Geoespacial
- Lee 1.Consolidado_Adecuado_<Periodo>.csv
- Asigna Colonia y corrige Ciudad usando GeoJSON de colonias
- Propiedades sin colonia -> Datos_Filtrados/Eliminados/<Periodo>/sin_colonia_<Periodo>.csv
- Propiedades con lat/lng "Desconocido" -> Datos_Filtrados/Eliminados/<Periodo>/coordenadas_desconocido_<Periodo>.csv
- Salida: 2.Consolidado_ConColonia_<Periodo>.csv
"""
from __future__ import annotations
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from esdata.utils.paths import path_consolidados, ensure_dir, path_base
from esdata.utils.io import read_csv, write_csv
from esdata.utils.logging_setup import get_logger

log = get_logger('step2')

COLONIAS_FILES = {
    'Gdl': 'N1_Tratamiento/Geolocalizacion/Colonias/colonias-Guadalajara.geojson',
    'Zap': 'N1_Tratamiento/Geolocalizacion/Colonias/colonias-Zapopan.geojson'
}

def cargar_colonias():
    frames = []
    crs_ref = None
    for ciudad, fpath in COLONIAS_FILES.items():
        abs_path = path_base(fpath)
        if not os.path.exists(abs_path):
            log.warning(f'No existe GeoJSON colonias {abs_path}')
            continue
        gdf = gpd.read_file(abs_path)
        if gdf.empty:
            log.warning(f'GeoJSON sin features: {abs_path}')
            continue
        if gdf.crs is None:
            # Asumimos WGS84 si no se especifica
            gdf.set_crs(epsg=4326, inplace=True)
        if crs_ref is None:
            crs_ref = gdf.crs
        elif gdf.crs != crs_ref:
            gdf = gdf.to_crs(crs_ref)
        gdf['__Ciudad_ref'] = ciudad
        frames.append(gdf)
    if not frames:
        raise FileNotFoundError('No se pudo cargar ningún geojson de colonias')
    colonias = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry='geometry', crs=crs_ref)
    if colonias.crs is None or colonias.crs.to_epsg() != 4326:
        colonias = colonias.to_crs(4326)
    return colonias

def completar_id_con_ubicacion(df: pd.DataFrame):
    """Completa el ID agregando Ciudad y Colonia al inicio"""
    
    def format_text_field(val, min_chars=3, max_chars=4):
        """Formatea campos de texto (Ciudad, Colonia)"""
        if pd.isna(val) or val is None:
            return "0" * min_chars
        s = str(val).strip()
        if s == '' or s.lower() in ['desconocido', 'desconocida']:
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
    
    def completar_id_row(row):
        """Completa el ID de una fila con ciudad y colonia"""
        id_actual = str(row.get('id', ''))
        if id_actual == '' or pd.isna(row.get('id')):
            return id_actual
        
        # Si el ID ya tiene formato completo (contiene guiones y underscores en posiciones esperadas), no modificar
        if len(id_actual.split('_')) >= 4 and len(id_actual.split('-')) >= 3:
            return id_actual
        
        # Formatear ciudad y colonia
        ciudad = format_text_field(row.get('Ciudad'), 3, 4)
        colonia = format_text_field(row.get('Colonia'), 3, 4)
        
        # Agregar ciudad y colonia al inicio del ID
        # Formato final: Ciudad-Colonia_id_actual
        return f"{ciudad}-{colonia}_{id_actual}"
    
    # Aplicar la función a todas las filas
    df['id'] = df.apply(completar_id_row, axis=1)
    
    return df

def geocodificar(df: pd.DataFrame, colonias_gdf: gpd.GeoDataFrame):
    # Identificar coordenadas "Desconocido" (como string)
    coord_desconocido_mask = ((df['longitud'].astype(str).str.lower() == 'desconocido') | 
                              (df['latitud'].astype(str).str.lower() == 'desconocido'))
    
    # Separar filas con coordenadas válidas (no NaN y no "Desconocido")
    coord_mask = (df['longitud'].notna() & df['latitud'].notna() & ~coord_desconocido_mask)
    df_valid = df[coord_mask].copy()
    
    if len(df_valid) > 0:
        gdf_pts = gpd.GeoDataFrame(
            df_valid,
            geometry=gpd.points_from_xy(df_valid['longitud'], df_valid['latitud']),
            crs='EPSG:4326'
        )
        joined = gpd.sjoin(gdf_pts, colonias_gdf, predicate='within', how='left')
        df.loc[coord_mask, 'Colonia'] = joined['NOMCOL1'].values
        # Actualizar ciudad solo cuando tengamos match de colonia
        ciudad_match_mask = coord_mask & df['Colonia'].notna()
        if '__Ciudad_ref' in joined.columns:
            df.loc[ciudad_match_mask, 'Ciudad'] = joined.loc[joined['NOMCOL1'].notna(), '__Ciudad_ref'].values
    
    return df, coord_desconocido_mask

def run(periodo):
    input_path = os.path.join(path_consolidados(), periodo, f'1.Consolidado_Adecuado_{periodo}.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)
    df = read_csv(input_path)
    colonias = cargar_colonias()
    
    # Procesar geocodificación
    df2, coord_desconocido_mask = geocodificar(df, colonias)
    
    # Identificar propiedades problemáticas (mejorado)
    sin_colonia_mask = (
        df2['Colonia'].isna() | 
        (df2['Colonia'].astype(str).str.strip() == '') |
        (df2['Colonia'].astype(str).str.lower() == 'desconocido')
    )
    sin_colonia = sin_colonia_mask.sum()
    
    sin_ciudad_mask = (
        df2['Ciudad'].isna() | 
        (df2['Ciudad'].astype(str).str.strip() == '') |
        (df2['Ciudad'].astype(str).str.lower() == 'desconocido')
    )
    sin_ciudad = sin_ciudad_mask.sum()
    
    coord_desconocido = coord_desconocido_mask.sum()
    
    log.info(f'Propiedades sin colonia válida: {sin_colonia}')
    log.info(f'Propiedades sin ciudad válida: {sin_ciudad}')
    log.info(f'Propiedades con coordenadas Desconocido: {coord_desconocido}')
    
    # Crear directorio para eliminados
    elim_dir = ensure_dir(path_base('Datos_Filtrados','Eliminados', periodo))
    
    # Guardar propiedades sin colonia válida (incluyendo "Desconocido")
    if sin_colonia > 0:
        df_sin_colonia = df2[sin_colonia_mask].copy()
        write_csv(df_sin_colonia, os.path.join(elim_dir, f'sin_colonia_{periodo}.csv'))
        log.info(f'Guardadas {sin_colonia} propiedades sin colonia válida en: sin_colonia_{periodo}.csv')
    
    # Guardar propiedades sin ciudad válida (incluyendo "Desconocido")
    if sin_ciudad > 0:
        df_sin_ciudad = df2[sin_ciudad_mask].copy()
        write_csv(df_sin_ciudad, os.path.join(elim_dir, f'sin_ciudad_{periodo}.csv'))
        log.info(f'Guardadas {sin_ciudad} propiedades sin ciudad válida en: sin_ciudad_{periodo}.csv')
    
    # Guardar propiedades con coordenadas Desconocido
    if coord_desconocido > 0:
        df_coord_desconocido = df2[coord_desconocido_mask].copy()
        write_csv(df_coord_desconocido, os.path.join(elim_dir, f'coordenadas_desconocido_{periodo}.csv'))
        log.info(f'Guardadas {coord_desconocido} propiedades con coordenadas Desconocido en: coordenadas_desconocido_{periodo}.csv')
    
    # FILTRAR: Eliminar propiedades sin colonia válida y con coordenadas desconocidas
    # Definir máscara para colonias válidas (no NaN, no 'Desconocido', no vacío)
    colonia_valida_mask = (
        df2['Colonia'].notna() & 
        (df2['Colonia'].astype(str).str.strip() != '') &
        (df2['Colonia'].astype(str).str.lower() != 'desconocido')
    )
    
    # También filtrar ciudades válidas
    ciudad_valida_mask = (
        df2['Ciudad'].notna() & 
        (df2['Ciudad'].astype(str).str.strip() != '') &
        (df2['Ciudad'].astype(str).str.lower() != 'desconocido')
    )
    
    # Filtro combinado: coordenadas válidas Y colonia válida Y ciudad válida
    df_final = df2[~coord_desconocido_mask & colonia_valida_mask & ciudad_valida_mask].copy()
    
    propiedades_eliminadas = len(df2) - len(df_final)
    log.info(f'Propiedades eliminadas del archivo final: {propiedades_eliminadas}')
    log.info(f'  - Con coordenadas Desconocido: {coord_desconocido_mask.sum()}')
    log.info(f'  - Sin colonia válida: {(~colonia_valida_mask).sum()}')
    log.info(f'  - Sin ciudad válida: {(~ciudad_valida_mask).sum()}')
    log.info(f'Propiedades que pasan al archivo final: {len(df_final)}')
    
    # Completar ID con Ciudad y Colonia para las propiedades válidas
    df_final = completar_id_con_ubicacion(df_final)
    log.info('IDs completados con información de ubicación (Ciudad-Colonia)')
    
    # Guardar resultado principal (solo propiedades con colonia válida)
    out_dir = ensure_dir(os.path.join(path_consolidados(), periodo))
    out_path = os.path.join(out_dir, f'2.Consolidado_ConColonia_{periodo}.csv')
    write_csv(df_final, out_path)
    
    return out_path

if __name__=='__main__':
    import sys, datetime as _dt
    per = sys.argv[1] if len(sys.argv)>1 else _dt.datetime.now().strftime('%b%y')
    run(per)
