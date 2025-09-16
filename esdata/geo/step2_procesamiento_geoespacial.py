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
    
    # Identificar propiedades problemáticas
    sin_colonia = df2['Colonia'].isna().sum()
    coord_desconocido = coord_desconocido_mask.sum()
    
    log.info(f'Propiedades sin colonia: {sin_colonia}')
    log.info(f'Propiedades con coordenadas Desconocido: {coord_desconocido}')
    
    # Crear directorio para eliminados
    elim_dir = ensure_dir(path_base('Datos_Filtrados','Eliminados', periodo))
    
    # Guardar propiedades sin colonia
    if sin_colonia > 0:
        df_sin_colonia = df2[df2['Colonia'].isna()].copy()
        write_csv(df_sin_colonia, os.path.join(elim_dir, f'sin_colonia_{periodo}.csv'))
        log.info(f'Guardadas {sin_colonia} propiedades sin colonia en: sin_colonia_{periodo}.csv')
    
    # Guardar propiedades con coordenadas Desconocido
    if coord_desconocido > 0:
        df_coord_desconocido = df2[coord_desconocido_mask].copy()
        write_csv(df_coord_desconocido, os.path.join(elim_dir, f'coordenadas_desconocido_{periodo}.csv'))
        log.info(f'Guardadas {coord_desconocido} propiedades con coordenadas Desconocido en: coordenadas_desconocido_{periodo}.csv')
    
    # Marcar como "Desconocida" las propiedades sin colonia para el archivo final
    df2.loc[df2['Colonia'].isna(), 'Colonia'] = 'Desconocida'
    
    # Guardar resultado principal
    out_dir = ensure_dir(os.path.join(path_consolidados(), periodo))
    out_path = os.path.join(out_dir, f'2.Consolidado_ConColonia_{periodo}.csv')
    write_csv(df2, out_path)
    
    return out_path

if __name__=='__main__':
    import sys, datetime as _dt
    per = sys.argv[1] if len(sys.argv)>1 else _dt.datetime.now().strftime('%b%y')
    run(per)
