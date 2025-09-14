"""Paso 8: Tabla de Resumen por Colonia
Genera dos CSV por combinación Ciudad-Operacion-Tipo:
    - *_inicial_: todas las colonias con métricas min/mean/max simple
    - *_final_: solo colonias con >=5 propiedades aplicando árbol de decisión media vs mediana

Colonias con <5 se envían a Datos_Filtrados/Esperando/<Periodo>/
Salida: N5_Resultados/Nivel_1/CSV/Tablas/<Periodo>/<Ciudad>_<Oper>_<Tipo>_<Periodo>_[inicial|final].csv

Uso CLI:
        python -m esdata.estadistica.step8_resumen_colonias <Periodo>
Si no se proporciona <Periodo>, se usa el periodo actual (mes abreviado + año, ej. Sep25).
"""
from __future__ import annotations
import os, re
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

def run(periodo: str):
    base_num = os.path.join(path_results_level(1), f'0.Final_Num_{periodo}.csv')
    if not os.path.exists(base_num):
        raise FileNotFoundError(base_num)
    df = read_csv(base_num)
    required = {'Ciudad','operacion','tipo_propiedad','Colonia','id'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Faltan columnas: {missing}')
    tablas_dir = path_resultados_tablas_periodo(periodo)
    esperando_dir = path_esperando(periodo)
    combos = df[['Ciudad','operacion','tipo_propiedad']].drop_duplicates()
    for _, combo in combos.iterrows():
        ciudad = combo['Ciudad']; oper = combo['operacion']; tipo = combo['tipo_propiedad']
        ciudad_s = _sanitize(ciudad)
        oper_s = _sanitize(oper)
        tipo_s = _sanitize(tipo)
        sub = df[(df['Ciudad']==ciudad) & (df['operacion']==oper) & (df['tipo_propiedad']==tipo)]
        ini = resumen_inicial(sub, periodo, ciudad, oper, tipo)
        fin = resumen_final(sub, periodo, ciudad, oper, tipo, esperando_dir)
        ini_path = os.path.join(tablas_dir, f'{ciudad_s}_{oper_s}_{tipo_s}_{periodo}_inicial.csv')
        fin_path = os.path.join(tablas_dir, f'{ciudad_s}_{oper_s}_{tipo_s}_{periodo}_final.csv')
        write_csv(ini, ini_path)
        write_csv(fin, fin_path)
        log.info(f'Resumen colonias {ciudad}-{oper}-{tipo}: inicial {len(ini)} final {len(fin)} -> archivos {os.path.basename(ini_path)}, {os.path.basename(fin_path)}')
    log.info('Paso 8 completado')

if __name__=='__main__':
    import sys
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        run(periodo_actual())