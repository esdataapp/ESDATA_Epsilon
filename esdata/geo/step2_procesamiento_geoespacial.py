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
    log.info('=' * 80)
    log.info('🌍 INICIANDO STEP 2: PROCESAMIENTO GEOESPACIAL')
    log.info('=' * 80)
    log.info(f'📅 Periodo: {periodo}')
    
    input_path = os.path.join(path_consolidados(), periodo, f'1.Consolidado_Adecuado_{periodo}.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)
    
    log.info(f'📁 Cargando datos de: {input_path}')
    df = read_csv(input_path)
    initial_count = len(df)
    log.info(f'✅ Propiedades cargadas: {initial_count:,}')
    
    # Estadísticas iniciales
    coords_validas = (df['longitud'].notna() & df['latitud'].notna()).sum()
    log.info(f'📍 Propiedades con coordenadas iniciales: {coords_validas:,}')
    
    log.info('🗺️ Cargando datos de colonias...')
    colonias = cargar_colonias()
    log.info(f'✅ Colonias cargadas: {len(colonias):,} polígonos')
    
    # Procesar geocodificación
    log.info('🔄 Iniciando proceso de geocodificación...')
    df2, coord_desconocido_mask = geocodificar(df, colonias)
    
    # Estadísticas de geocodificación
    colonias_asignadas = df2['Colonia'].notna().sum()
    ciudades_asignadas = df2['Ciudad'].notna().sum()
    
    log.info('📈 RESULTADOS DE GEOCODIFICACIÓN:')
    log.info(f'   • Colonias asignadas: {colonias_asignadas:,}')
    log.info(f'   • Ciudades asignadas: {ciudades_asignadas:,}')
    
    # Identificar propiedades problemáticas (LÓGICA COHERENTE)
    # Si no tiene colonia válida, automáticamente no tiene ciudad válida
    sin_colonia_mask = (
        df2['Colonia'].isna() | 
        (df2['Colonia'].astype(str).str.strip() == '') |
        (df2['Colonia'].astype(str).str.lower() == 'desconocido')
    )
    
    # CORRECCIÓN LÓGICA: Si no hay colonia, no puede haber ciudad válida
    # Marcar ciudad como "Desconocido" cuando no hay colonia válida
    df2.loc[sin_colonia_mask, 'Ciudad'] = 'Desconocido'
    
    # Ahora las máscaras deben ser idénticas por lógica
    sin_ciudad_mask = (
        df2['Ciudad'].isna() | 
        (df2['Ciudad'].astype(str).str.strip() == '') |
        (df2['Ciudad'].astype(str).str.lower() == 'desconocido')
    )
    
    sin_colonia = sin_colonia_mask.sum()
    sin_ciudad = sin_ciudad_mask.sum()
    coord_desconocido = coord_desconocido_mask.sum()
    
    # Verificar coherencia lógica
    if sin_colonia != sin_ciudad:
        log.warning(f'⚠️ INCONSISTENCIA DETECTADA: sin_colonia ({sin_colonia}) ≠ sin_ciudad ({sin_ciudad})')
        log.warning('Forzando coherencia lógica: sin colonia → sin ciudad')
        
        # Forzar coherencia: todas las propiedades sin colonia no tienen ciudad
        df2.loc[sin_colonia_mask, 'Ciudad'] = 'Desconocido'
        sin_ciudad_mask = sin_colonia_mask.copy()  # Hacer máscaras idénticas
        sin_ciudad = sin_colonia
    
    log.info('⚠️ PROPIEDADES PROBLEMÁTICAS IDENTIFICADAS:')
    log.info(f'   • Sin colonia válida: {sin_colonia:,}')
    log.info(f'   • Sin ciudad válida: {sin_ciudad:,}') 
    log.info(f'   • Con coordenadas "Desconocido": {coord_desconocido:,}')
    log.info(f'   ✅ Coherencia lógica: {"SÍ" if sin_colonia == sin_ciudad else "NO"}')
    
    # Crear directorio para eliminados
    elim_dir = ensure_dir(path_base('Datos_Filtrados','Eliminados', periodo))
    log.info(f'📁 Directorio de eliminados: {elim_dir}')
    
    # Guardar propiedades problemáticas
    archivos_eliminados = []
    
    # Como ahora sin_colonia == sin_ciudad por coherencia lógica,
    # guardamos un solo archivo unificado
    if sin_colonia > 0:
        df_problematicas = df2[sin_colonia_mask].copy()
        archivo_problematicas = os.path.join(elim_dir, f'sin_colonia_ciudad_{periodo}.csv')
        write_csv(df_problematicas, archivo_problematicas)
        archivos_eliminados.append(f'sin_colonia_ciudad_{periodo}.csv')
        log.info(f'💾 Guardadas {sin_colonia:,} propiedades sin colonia/ciudad válida')
        
        # Mantener compatibilidad con archivos existentes (opcional)
        if sin_colonia != sin_ciudad:  # Solo si hubo diferencia original
            archivo_colonia = os.path.join(elim_dir, f'sin_colonia_{periodo}.csv')
            archivo_ciudad = os.path.join(elim_dir, f'sin_ciudad_{periodo}.csv')
            write_csv(df_problematicas, archivo_colonia)
            write_csv(df_problematicas, archivo_ciudad)
            archivos_eliminados.extend([f'sin_colonia_{periodo}.csv', f'sin_ciudad_{periodo}.csv'])
            log.info(f'💾 Archivos separados generados para compatibilidad')
    
    if coord_desconocido > 0:
        df_coord_desconocido = df2[coord_desconocido_mask].copy()
        archivo_coords = os.path.join(elim_dir, f'coordenadas_desconocido_{periodo}.csv')
        write_csv(df_coord_desconocido, archivo_coords)
        archivos_eliminados.append(f'coordenadas_desconocido_{periodo}.csv')
        log.info(f'💾 Guardadas {coord_desconocido:,} propiedades con coordenadas Desconocido')
    
    # FILTRAR: Eliminar propiedades sin colonia válida y con coordenadas desconocidas
    log.info('🔍 Aplicando filtros de calidad...')
    
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
    
    log.info('📊 RESUMEN DE FILTRADO:')
    log.info(f'   • Propiedades eliminadas total: {propiedades_eliminadas:,}')
    log.info(f'   • Por coordenadas Desconocido: {coord_desconocido_mask.sum():,}')
    log.info(f'   • Por colonia inválida: {(~colonia_valida_mask).sum():,}')
    log.info(f'   • Por ciudad inválida: {(~ciudad_valida_mask).sum():,}')
    log.info(f'   • Propiedades que pasan: {len(df_final):,}')
    log.info(f'   • Tasa de retención: {(len(df_final)/initial_count*100):.1f}%')
    
    if archivos_eliminados:
        log.info(f'📁 Archivos de propiedades eliminadas: {archivos_eliminados}')
    
    # Completar ID con Ciudad y Colonia para las propiedades válidas
    log.info('🔗 Completando IDs con información de ubicación...')
    df_final = completar_id_con_ubicacion(df_final)
    
    # Estadísticas de IDs completados
    ids_completados = df_final['id'].str.contains('-', na=False).sum()
    log.info(f'✅ IDs completados con ubicación: {ids_completados:,}')
    
    # Guardar resultado principal (solo propiedades con colonia válida)
    out_dir = ensure_dir(os.path.join(path_consolidados(), periodo))
    out_path = os.path.join(out_dir, f'2.Consolidado_ConColonia_{periodo}.csv')
    write_csv(df_final, out_path)
    
    log.info('💾 ARCHIVO FINAL GENERADO:')
    log.info(f'   • Ruta: {out_path}')
    log.info(f'   • Tamaño: {os.path.getsize(out_path) / 1024 / 1024:.2f} MB')
    log.info(f'   • Propiedades válidas: {len(df_final):,}')
    
    # Resumen por ciudad y tipo
    if not df_final.empty:
        log.info('🏙️ DISTRIBUCIÓN FINAL POR CIUDAD:')
        for ciudad, count in df_final['Ciudad'].value_counts().head(10).items():
            log.info(f'   • {ciudad}: {count:,} propiedades')
        
        log.info('🏠 DISTRIBUCIÓN POR TIPO DE PROPIEDAD:')
        for tipo, count in df_final['tipo_propiedad'].value_counts().items():
            log.info(f'   • {tipo}: {count:,} propiedades')
    
    log.info('✅ STEP 2 COMPLETADO EXITOSAMENTE')
    log.info('=' * 80)
    
    return out_path

if __name__=='__main__':
    import sys, datetime as _dt
    per = sys.argv[1] if len(sys.argv)>1 else _dt.datetime.now().strftime('%b%y')
    run(per)
