"""Paso 8: Tabla de Resumen por Colonia
Genera dos CSV por combinación Ciudad-Operacion-Tipo:
    - *_inicial_: todas las colonias con métricas min/mean/max simple
    - *_final_: solo colonias con >=5 propiedades aplicando árbol de decisión media vs mediana

Colonias con <5 se envían a Datos_Filtrados/Esperando/<Periodo>/
Salida: N5_Resultados/Nive    # GENERAR FINAL_PUNTOS PRIMERO con TODAS las propiedades (sin filtros)
    log.info('📍 Generando archivo Final_Puntos con TODAS las propiedades...')
    generar_final_puntos(df, periodo)
    
    # GENERAR TABLERO MAESTRO con TODAS las colonias del GeoJSON
    log.info('🗺️ Generando tablero maestro con TODAS las colonias...')
    generar_tablero_maestro_colonias(df, periodo)/CSV/Tablas/<Periodo>/<Ciudad>_<Oper>_<Tipo>_<Periodo>_[inicial|final].csv

Uso CLI:
        python -m esdata.estadistica.step8_resumen_colonias <Periodo>
Si no se proporciona <Periodo>, se usa el periodo actual (mes abreviado + año, ej. Sep25).
"""
from __future__ import annotations
import os, re, json
import pandas as pd
from esdata.utils.paths import (
    path_results_level, path_resultados_tablas_periodo, path_esperando,
    path_eliminados, ensure_dir, periodo_actual
)
from esdata.utils.io import read_csv, write_csv
from esdata.utils.logging_setup import get_logger

log = get_logger('step8')

METRIC_VARS = ['precio','area_m2','PxM2']

def _sanitize(text: str|None) -> str:
    """Sanear componentes que se usarán en nombres de archivos.
    Reemplaza espacios, barras y caracteres no alfanuméricos por guion bajo y limita longitud.
    """
    if text is None:
        return 'Desconocido'
    t = str(text).strip()
    t = re.sub(r'[\\/]+', '_', t)
    t = re.sub(r'\s+', '_', t)
    t = re.sub(r'[^A-Za-z0-9_\-]', '_', t)
    return t[:40] if len(t)>40 else t

def decision_method(n: int, skew: float|None) -> str:
    if n < 5:
        return 'insuficiente'
    if n < 10:
        return 'mediana_rango'
    if skew is None or pd.isna(skew):
        return 'media_desv' if n>=30 else 'mediana_IQR'
    if abs(skew) > 1:
        return 'mediana_IQR'
    if -0.5 <= skew <= 0.5 and n>=30:
        return 'media_desv'
    return 'mediana_IQR'

def resumen_inicial(df: pd.DataFrame, periodo: str, ciudad: str, oper: str, tipo: str) -> pd.DataFrame:
    grp = df.groupby('Colonia')
    rows = []
    for colonia, sub in grp:
        row = {
            'Periodo': periodo,
            'Ciudad': ciudad,
            'Operacion': oper,
            'Tipo': tipo,
            'Colonia': colonia,
            'n': len(sub)
        }
        for v in METRIC_VARS:
            if v in sub.columns:
                serie = sub[v].dropna().astype(float)
                if serie.empty:
                    row[f'{v}_min']=None; row[f'{v}_mean']=None; row[f'{v}_max']=None
                else:
                    row[f'{v}_min']=serie.min(); row[f'{v}_mean']=serie.mean(); row[f'{v}_max']=serie.max()
        rows.append(row)
    return pd.DataFrame(rows)

def resumen_final(df: pd.DataFrame, periodo: str, ciudad: str, oper: str, tipo: str, esperando_dir: str) -> pd.DataFrame:
    grp = df.groupby('Colonia')
    final_rows = []
    esperar_rows = []
    for colonia, sub in grp:
        n = len(sub)
        if n < 5:
            # Enviar a esperando con toda su info
            esperar_rows.append(sub)
            continue
        row = {
            'Periodo': periodo,
            'Ciudad': ciudad,
            'Operacion': oper,
            'Tipo': tipo,
            'Colonia': colonia,
            'n': n
        }
        for v in METRIC_VARS:
            if v in sub.columns:
                serie = sub[v].dropna().astype(float)
                if serie.empty:
                    continue
                skew = pd.to_numeric(pd.Series([serie.skew()]), errors='coerce').iloc[0] if len(serie)>2 else None
                metodo = decision_method(n, skew)
                if metodo in ('mediana_rango','mediana_IQR','mediana_IQR'):
                    row[f'{v}_representativo'] = serie.median()
                else:
                    row[f'{v}_representativo'] = serie.mean()
                row[f'{v}_min']=serie.min(); row[f'{v}_max']=serie.max()
                row[f'{v}_skew']=skew
                row[f'{v}_metodo']=metodo
        final_rows.append(row)
    if esperar_rows:
        esperar_df = pd.concat(esperar_rows, ignore_index=True)
        c_s = _sanitize(ciudad); o_s = _sanitize(oper); t_s = _sanitize(tipo)
        esperar_path = os.path.join(esperando_dir, f'esperando_{c_s}_{o_s}_{t_s}_{periodo}.csv')
        write_csv(esperar_df, esperar_path)
    return pd.DataFrame(final_rows)

def generar_tablero_maestro_colonias(df: pd.DataFrame, periodo: str):
    """Generar tablero maestro con TODAS las colonias del GeoJSON (tengan datos o no)"""
    log.info('🗺️ Generando tablero maestro con TODAS las colonias...')
    
    # Importar función para cargar colonias
    from esdata.geo.step2_procesamiento_geoespacial import cargar_colonias
    
    # Cargar todas las colonias del GeoJSON
    colonias_gdf = cargar_colonias()
    log.info(f'📍 Colonias del GeoJSON cargadas: {len(colonias_gdf):,}')
    
    # Obtener todas las combinaciones únicas de operación y tipo de propiedad de los datos
    operaciones = df['operacion'].unique()
    tipos_propiedad = df['tipo_propiedad'].unique()
    
    log.info(f'🔍 Operaciones encontradas: {list(operaciones)}')
    log.info(f'🏠 Tipos de propiedad encontrados: {list(tipos_propiedad)}')
    
    # Crear base de datos con todas las colonias y sus ciudades
    colonias_base = []
    for _, colonia_row in colonias_gdf.iterrows():
        colonia_name = colonia_row.get('NOMCOL1', 'Desconocido')
        ciudad_name = colonia_row.get('__Ciudad_ref', 'Desconocido')  # Asumiendo que tienes este campo
        
        colonias_base.append({
            'Ciudad': ciudad_name,
            'Colonia': colonia_name
        })
    
    colonias_df = pd.DataFrame(colonias_base).drop_duplicates()
    log.info(f'📋 Colonias únicas procesadas: {len(colonias_df)}')
    
    # Crear combinaciones completas: Todas las colonias x Todas las operaciones x Todos los tipos
    tablero_completo = []
    
    for _, colonia_info in colonias_df.iterrows():
        for operacion in operaciones:
            for tipo_propiedad in tipos_propiedad:
                # Base del registro
                registro = {
                    'Periodo': periodo,
                    'Ciudad': colonia_info['Ciudad'],
                    'Colonia': colonia_info['Colonia'],
                    'Operacion': operacion,
                    'Tipo': tipo_propiedad,
                    'tiene_datos': False,
                    'n': 0
                }
                
                # Buscar datos reales para esta combinación
                datos_colonia = df[
                    (df['Ciudad'] == colonia_info['Ciudad']) & 
                    (df['Colonia'] == colonia_info['Colonia']) & 
                    (df['operacion'] == operacion) & 
                    (df['tipo_propiedad'] == tipo_propiedad)
                ]
                
                if len(datos_colonia) > 0:
                    registro['tiene_datos'] = True
                    registro['n'] = len(datos_colonia)
                    
                    # Calcular métricas para variables numéricas
                    for var in METRIC_VARS:
                        if var in datos_colonia.columns:
                            serie = datos_colonia[var].dropna().astype(float)
                            if not serie.empty:
                                registro[f'{var}_min'] = serie.min()
                                registro[f'{var}_mean'] = serie.mean()
                                registro[f'{var}_max'] = serie.max()
                                registro[f'{var}_median'] = serie.median()
                                registro[f'{var}_std'] = serie.std()
                            else:
                                for suffix in ['min', 'mean', 'max', 'median', 'std']:
                                    registro[f'{var}_{suffix}'] = None
                        else:
                            for suffix in ['min', 'mean', 'max', 'median', 'std']:
                                registro[f'{var}_{suffix}'] = None
                else:
                    # No hay datos para esta combinación
                    for var in METRIC_VARS:
                        for suffix in ['min', 'mean', 'max', 'median', 'std']:
                            registro[f'{var}_{suffix}'] = None
                
                tablero_completo.append(registro)
    
    # Crear DataFrame final
    tablero_df = pd.DataFrame(tablero_completo)
    
    # Estadísticas del tablero
    total_combinaciones = len(tablero_df)
    combinaciones_con_datos = tablero_df['tiene_datos'].sum()
    combinaciones_sin_datos = total_combinaciones - combinaciones_con_datos
    
    log.info('📊 ESTADÍSTICAS DEL TABLERO MAESTRO:')
    log.info(f'   • Total combinaciones posibles: {total_combinaciones:,}')
    log.info(f'   • Combinaciones con datos: {combinaciones_con_datos:,}')
    log.info(f'   • Combinaciones sin datos: {combinaciones_sin_datos:,}')
    log.info(f'   • Cobertura: {(combinaciones_con_datos/total_combinaciones*100):.1f}%')
    
    # Análisis por ciudad
    log.info('🏙️ COBERTURA POR CIUDAD:')
    cobertura_ciudad = tablero_df.groupby('Ciudad').agg({
        'tiene_datos': ['count', 'sum']
    }).round(2)
    cobertura_ciudad.columns = ['total_posibles', 'con_datos']
    cobertura_ciudad['cobertura_pct'] = (cobertura_ciudad['con_datos'] / cobertura_ciudad['total_posibles'] * 100).round(1)
    
    for ciudad, stats in cobertura_ciudad.head(10).iterrows():
        log.info(f'   • {ciudad}: {stats["con_datos"]:.0f}/{stats["total_posibles"]:.0f} ({stats["cobertura_pct"]}%)')
    
    # Guardar archivo
    resumen_dir = ensure_dir(os.path.join(path_results_level(1), 'Resumen', periodo))
    tablero_path = os.path.join(resumen_dir, f'Final_Resumen_{periodo}.csv')
    write_csv(tablero_df, tablero_path)
    
    log.info('💾 TABLERO MAESTRO GENERADO:')
    log.info(f'   • Ruta: {tablero_path}')
    log.info(f'   • Registros: {len(tablero_df):,}')
    log.info(f'   • Tamaño: {os.path.getsize(tablero_path) / 1024 / 1024:.2f} MB')
    
    return tablero_path

def generar_final_puntos(df: pd.DataFrame, periodo: str):
    """Generar archivo Final_Puntos con TODAS las propiedades (sin filtros de colonia)"""
    # Variables específicas requeridas para puntos
    puntos_vars = ['id', 'Ciudad', 'Colonia', 'operacion', 'tipo_propiedad', 
                   'area_m2', 'precio', 'longitud', 'latitud', 'PxM2', 'Fecha_Scrap']
    
    # Filtrar solo las variables que existen en el DataFrame
    existing_vars = [var for var in puntos_vars if var in df.columns]
    
    if len(existing_vars) != len(puntos_vars):
        missing_vars = set(puntos_vars) - set(existing_vars)
        log.warning(f'Variables faltantes para Final_Puntos: {missing_vars}')
    
    # Crear DataFrame con las variables disponibles (SIN FILTROS)
    puntos_df = df[existing_vars].copy()
    
    # Crear directorio de puntos
    puntos_dir = ensure_dir(os.path.join(path_results_level(1), 'Puntos', periodo))
    puntos_path = os.path.join(puntos_dir, f'Final_Puntos_{periodo}.csv')
    
    # Guardar archivo
    write_csv(puntos_df, puntos_path)
    
    log.info(f'✅ Final_Puntos generado: {len(puntos_df)} propiedades COMPLETAS (sin filtros de colonia) con {len(existing_vars)} variables')
    log.info(f'📁 Archivo guardado: {puntos_path}')
    
    return puntos_path

def generar_resumen_consolidado(df: pd.DataFrame, periodo: str):
    """Generar archivo consolidado con TODAS las colonias y combinaciones"""
    log.info('📋 Generando resumen consolidado de todas las colonias...')
    
    # Obtener todas las combinaciones Ciudad-Operación-Tipo
    combos = df[['Ciudad','operacion','tipo_propiedad']].drop_duplicates()
    
    todos_resumenes = []
    total_combos = len(combos)
    
    for i, (_, combo) in enumerate(combos.iterrows(), 1):
        ciudad = combo['Ciudad']
        oper = combo['operacion'] 
        tipo = combo['tipo_propiedad']
        
        # Filtrar datos para esta combinación
        sub = df[(df['Ciudad']==ciudad) & (df['operacion']==oper) & (df['tipo_propiedad']==tipo)]
        
        if len(sub) == 0:
            continue
            
        log.info(f'   📊 Procesando resumen ({i}/{total_combos}): {ciudad}-{oper}-{tipo}')
        
        # Generar resumen inicial para esta combinación (SIN filtros de colonia)
        resumen = resumen_inicial(sub, periodo, ciudad, oper, tipo)
        todos_resumenes.append(resumen)
    
    # Consolidar todos los resúmenes
    if todos_resumenes:
        resumen_consolidado = pd.concat(todos_resumenes, ignore_index=True)
    else:
        resumen_consolidado = pd.DataFrame()
    
    # Crear directorio de resumen
    resumen_dir = ensure_dir(os.path.join(path_results_level(1), 'Resumen', periodo))
    resumen_path = os.path.join(resumen_dir, f'Final_Resumen_{periodo}.csv')
    
    # Guardar archivo consolidado
    write_csv(resumen_consolidado, resumen_path)
    
    # Estadísticas del resumen
    if not resumen_consolidado.empty:
        total_colonias = len(resumen_consolidado)
        colonias_validas = len(resumen_consolidado[resumen_consolidado['n'] >= 5])
        colonias_esperando = len(resumen_consolidado[resumen_consolidado['n'] < 5])
        
        log.info('📈 RESUMEN CONSOLIDADO GENERADO:')
        log.info(f'   • Total de colonias: {total_colonias:,}')
        log.info(f'   • Colonias válidas (≥5 props): {colonias_validas:,}')
        log.info(f'   • Colonias en espera (<5 props): {colonias_esperando:,}')
        log.info(f'   • Combinaciones procesadas: {total_combos}')
        log.info(f'   • Archivo: {resumen_path}')
        
        # Top ciudades por número de colonias
        top_ciudades = resumen_consolidado['Ciudad'].value_counts().head(5)
        log.info('🏙️ TOP CIUDADES POR NÚMERO DE COLONIAS:')
        for ciudad, count in top_ciudades.items():
            log.info(f'   • {ciudad}: {count:,} colonias')
    else:
        log.warning('⚠️ No se generó resumen consolidado - sin datos')
    
    return resumen_path

def run(periodo: str):
    log.info('=' * 80)
    log.info('📊 INICIANDO STEP 8: RESUMEN POR COLONIAS Y GENERACIÓN DE PUNTOS')
    log.info('=' * 80)
    log.info(f'📅 Periodo: {periodo}')
    
    base_num = os.path.join(path_results_level(1), f'0.Final_Num_{periodo}.csv')
    if not os.path.exists(base_num):
        raise FileNotFoundError(base_num)
    
    log.info(f'📁 Cargando archivo final: {base_num}')
    df = read_csv(base_num)
    
    required = {'Ciudad','operacion','tipo_propiedad','Colonia','id'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Faltan columnas requeridas: {missing}')
    
    total_propiedades = len(df)
    log.info(f'✅ Propiedades cargadas: {total_propiedades:,}')
    
    # Estadísticas generales
    log.info('📈 ESTADÍSTICAS GENERALES:')
    log.info(f'   • Ciudades únicas: {df["Ciudad"].nunique()}')
    log.info(f'   • Colonias únicas: {df["Colonia"].nunique()}')
    log.info(f'   • Tipos de propiedad: {df["tipo_propiedad"].nunique()}')
    log.info(f'   • Operaciones: {df["operacion"].nunique()}')
    
    # GENERAR RESUMEN CONSOLIDADO PRIMERO (con TODAS las colonias)
    generar_resumen_consolidado(df, periodo)
    
    # GENERAR FINAL_PUNTOS con TODAS las propiedades (sin filtros)
    log.info('📍 Generando archivo Final_Puntos con TODAS las propiedades...')
    generar_final_puntos(df, periodo)
    
    # Continuar con el análisis estadístico por colonias (con filtros)
    log.info('📊 Iniciando análisis estadístico por colonias...')
    tablas_dir = path_resultados_tablas_periodo(periodo)
    esperando_dir = path_esperando(periodo)
    
    log.info(f'📁 Directorio de tablas: {tablas_dir}')
    log.info(f'📁 Directorio de esperando: {esperando_dir}')
    
    combos = df[['Ciudad','operacion','tipo_propiedad']].drop_duplicates()
    total_combos = len(combos)
    
    log.info(f'🔍 Combinaciones Ciudad-Operación-Tipo encontradas: {total_combos}')
    
    archivos_generados = []
    propiedades_esperando_total = 0
    
    for i, (_, combo) in enumerate(combos.iterrows(), 1):
        ciudad = combo['Ciudad']; oper = combo['operacion']; tipo = combo['tipo_propiedad']
        ciudad_s = _sanitize(ciudad)
        oper_s = _sanitize(oper)
        tipo_s = _sanitize(tipo)
        
        sub = df[(df['Ciudad']==ciudad) & (df['operacion']==oper) & (df['tipo_propiedad']==tipo)]
        
        log.info(f'📋 Procesando ({i}/{total_combos}): {ciudad}-{oper}-{tipo} ({len(sub):,} propiedades)')
        
        ini = resumen_inicial(sub, periodo, ciudad, oper, tipo)
        fin = resumen_final(sub, periodo, ciudad, oper, tipo, esperando_dir)
        
        ini_path = os.path.join(tablas_dir, f'{ciudad_s}_{oper_s}_{tipo_s}_{periodo}_inicial.csv')
        fin_path = os.path.join(tablas_dir, f'{ciudad_s}_{oper_s}_{tipo_s}_{periodo}_final.csv')
        
        write_csv(ini, ini_path)
        write_csv(fin, fin_path)
        
        archivos_generados.extend([os.path.basename(ini_path), os.path.basename(fin_path)])
        
        # Contar propiedades que van a "esperando" (colonias con <5 propiedades)
        colonias_pequenas = ini[ini['n'] < 5]
        if not colonias_pequenas.empty:
            propiedades_en_colonias_pequenas = colonias_pequenas['n'].sum()
            propiedades_esperando_total += propiedades_en_colonias_pequenas
            log.info(f'   ⏳ {len(colonias_pequenas)} colonias con <5 propiedades → {propiedades_en_colonias_pequenas} propiedades a esperando')
        
        log.info(f'   ✅ Generado: inicial({len(ini)} colonias) final({len(fin)} colonias válidas)')
    
    log.info('📊 RESUMEN FINAL DEL ANÁLISIS:')
    log.info(f'   • Archivos generados: {len(archivos_generados)}')
    log.info(f'   • Propiedades en colonias válidas (≥5): {total_propiedades - propiedades_esperando_total:,}')
    log.info(f'   • Propiedades en espera (<5 por colonia): {propiedades_esperando_total:,}')
    log.info(f'   • Tasa de aprovechamiento: {((total_propiedades - propiedades_esperando_total)/total_propiedades*100):.1f}%')
    
    log.info('✅ STEP 8 COMPLETADO EXITOSAMENTE')
    log.info('=' * 80)

if __name__=='__main__':
    import sys
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        run(periodo_actual())