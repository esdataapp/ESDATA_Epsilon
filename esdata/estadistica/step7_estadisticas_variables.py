"""Paso 7: Estadísticas de Variables Clave (Implementación Extendida F1)

Replica conceptualmente el set F1 para las variables: precio, area_m2, PxM2.
Entrada: 0.Final_Num_<Periodo>.csv
Salidas organizadas en:
  N2_Estadisticas/Estudios/<Periodo>/
      F1_Descriptivo_<Periodo>.csv (detalle completo)
      F1_Outliers_<Periodo>.csv (límites y conteos)
      F1_Normalidad_<Periodo>.csv (skew, kurtosis, shapiro)
  N2_Estadisticas/Resultados/<Periodo>/
      F1_Parametricos_<Periodo>.csv (coef. variación, IQR, rango, sugerencia método preliminar)
  N2_Estadisticas/Reportes/<Periodo>/
      F1_Descriptivo_Rep_<Periodo>.csv (resumen clave)
      F1_Outliers_Rep_<Periodo>.csv (resumen outliers)
      F1_Normalidad_Rep_<Periodo>.csv (resumen normalidad)
      Estadisticas_Global_<Periodo>.csv (consolidado para dashboard o lectura rápida)

Lógica adicional:
 - Recalcula PxM2 si falta.
 - Percentiles extendidos: 1,5,10,25,50,75,90,95,99
 - Moda, varianza, IQR, rango, coeficiente de variación.
 - Shapiro-Wilk (3 <= n <= 5000) para p-value formal.
 - Sugerencia preliminar de método representativo (media vs mediana) alineada a reglas Paso 10.
"""
from __future__ import annotations
import os, sys, argparse
from typing import Dict, Any
import pandas as pd
import numpy as np

# Asegurar raíz del proyecto en sys.path cuando se ejecuta directamente
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from esdata.utils.paths import (
    path_results_level, path_estadistica_estudios, path_estadistica_resultados, path_estadistica_reportes,
    ensure_dir, path_resultados_tablas_periodo
)
from esdata.utils.io import read_csv, write_csv
from esdata.utils.logging_setup import get_logger

log = get_logger('step7')

TARGET_VARS = ['precio','area_m2','PxM2']

PERCENTILES_EXT = [0.01,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.99]

def _ensure_pxm2(df: pd.DataFrame) -> pd.DataFrame:
    if 'PxM2' not in df.columns and {'precio','area_m2'} <= set(df.columns):
        mask = df['area_m2'].notna() & (df['area_m2']>0) & df['precio'].notna()
        df = df.copy()
        df['PxM2'] = None
        df.loc[mask,'PxM2'] = df.loc[mask,'precio']/df.loc[mask,'area_m2']
    return df

def _describe(df: pd.DataFrame, var: str) -> pd.DataFrame:
    serie = df[var].dropna().astype(float)
    if serie.empty:
        return pd.DataFrame([{ 'variable': var, 'count':0 }])
    stats: Dict[str, Any] = {}
    stats['variable'] = var
    stats['count'] = len(serie)
    stats['missing'] = df[var].isna().sum()
    stats['missing_pct'] = stats['missing']/len(df) if len(df)>0 else 0
    stats['mean'] = serie.mean()
    stats['median'] = serie.median()
    # Moda robusta (puede haber multiples)
    try:
        mode_vals = serie.mode()
        stats['mode'] = mode_vals.iloc[0] if not mode_vals.empty else None
    except Exception:
        stats['mode'] = None
    stats['std'] = serie.std(ddof=1)
    stats['var'] = serie.var(ddof=1)
    stats['min'] = serie.min()
    stats['max'] = serie.max()
    stats['range'] = stats['max'] - stats['min'] if stats['count']>0 else None
    # Percentiles extendidos
    for p in PERCENTILES_EXT:
        stats[f'p{int(p*100):02d}'] = float(serie.quantile(p))
    stats['iqr'] = stats['p75'] - stats['p25'] if 'p75' in stats and 'p25' in stats else None
    stats['coef_var_pct'] = (stats['std']/stats['mean']*100) if stats['mean'] not in (0,None) else None
    stats['skew'] = pd.to_numeric(pd.Series([serie.skew()]), errors='coerce').iloc[0]
    stats['kurtosis'] = pd.to_numeric(pd.Series([serie.kurt()]), errors='coerce').iloc[0]
    return pd.DataFrame([stats])

def _outliers_iqr(df: pd.DataFrame, var: str) -> pd.DataFrame:
    s = df[var].dropna().astype(float)
    if len(s)<4:
        return pd.DataFrame([{ 'variable': var, 'q1':np.nan, 'q3':np.nan, 'iqr':np.nan, 'lower':np.nan, 'upper':np.nan, 'outliers':0, 'ratio':0 }])
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5*iqr
    upper = q3 + 1.5*iqr
    mask = (s<lower) | (s>upper)
    outliers = s[mask]
    return pd.DataFrame([{
        'variable': var,
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'lower': lower,
        'upper': upper,
        'outliers': len(outliers),
        'ratio': len(outliers)/len(s) if len(s)>0 else 0
    }])

def _normality(df: pd.DataFrame, var: str) -> pd.DataFrame:
    from scipy.stats import shapiro
    s = df[var].dropna().astype(float)
    n = len(s)
    if n < 3:
        return pd.DataFrame([{'variable':var,'n':n,'skew':np.nan,'kurtosis':np.nan,'shapiro_stat':np.nan,'shapiro_p':np.nan,'approx_normal':False}])
    skew = pd.to_numeric(pd.Series([s.skew()]), errors='coerce').iloc[0]
    kurt = pd.to_numeric(pd.Series([s.kurt()]), errors='coerce').iloc[0]
    sh_stat = np.nan; sh_p = np.nan
    if 3 <= n <= 5000:
        try:
            sh_stat, sh_p = shapiro(s.sample(min(n, 5000), random_state=42))
        except Exception:
            pass
    approx = bool((abs(skew) < 1.0) and (abs(kurt) < 3.0) and (np.isnan(sh_p) or sh_p>0.05))
    return pd.DataFrame([{'variable':var,'n':n,'skew':skew,'kurtosis':kurt,'shapiro_stat':sh_stat,'shapiro_p':sh_p,'approx_normal':approx}])

def _suggest_method(row: pd.Series) -> str:
    n = row.get('count', 0)
    skew = row.get('skew', None)
    if n < 5:
        return 'no_estadistica'
    if n < 10:
        return 'mediana_rango'
    if skew is None or pd.isna(skew):
        return 'media_desv' if n>=30 else 'mediana_IQR'
    if abs(skew) > 1:
        return 'mediana_IQR'
    if -0.5 <= skew <= 0.5:
        return 'media_desv' if n>=30 else 'mediana_IQR'
    return 'mediana_IQR'

def run(periodo: str):
    num_path = os.path.join(path_results_level(1), f'0.Final_Num_{periodo}.csv')
    if not os.path.exists(num_path):
        raise FileNotFoundError(num_path)
    df = read_csv(num_path)
    df = _ensure_pxm2(df)
    estudios_dir = path_estadistica_estudios(periodo)
    resultados_dir = path_estadistica_resultados(periodo)
    reportes_dir = path_estadistica_reportes(periodo)
    ensure_dir(estudios_dir); ensure_dir(resultados_dir); ensure_dir(reportes_dir)
    # Filtrar target vars existentes
    vars_present = [v for v in TARGET_VARS if v in df.columns]
    desc_frames=[]; out_frames=[]; norm_frames=[]
    for v in vars_present:
        desc_frames.append(_describe(df,v))
        out_frames.append(_outliers_iqr(df,v))
        norm_frames.append(_normality(df,v))
    descriptivo = pd.concat(desc_frames, ignore_index=True) if desc_frames else pd.DataFrame()
    outliers = pd.concat(out_frames, ignore_index=True) if out_frames else pd.DataFrame()
    normalidad = pd.concat(norm_frames, ignore_index=True) if norm_frames else pd.DataFrame()

    # Sugerencia método preliminar (por variable global, sirve como referencia general)
    if not descriptivo.empty:
        descriptivo['metodo_sugerido_global'] = descriptivo.apply(_suggest_method, axis=1)

    # Guardar Estudios (detalle completo)
    write_csv(descriptivo, os.path.join(estudios_dir, f'F1_Descriptivo_{periodo}.csv'))
    write_csv(outliers, os.path.join(estudios_dir, f'F1_Outliers_{periodo}.csv'))
    write_csv(normalidad, os.path.join(estudios_dir, f'F1_Normalidad_{periodo}.csv'))

    # Resultados (parámetros clave por variable)
    if not descriptivo.empty and not outliers.empty and not normalidad.empty:
        resultados = descriptivo.merge(outliers[['variable','q1','q3','iqr','lower','upper','outliers','ratio']], on='variable', how='left')
        resultados = resultados.merge(normalidad[['variable','shapiro_stat','shapiro_p','approx_normal']], on='variable', how='left')
    else:
        resultados = pd.DataFrame()
    write_csv(resultados, os.path.join(resultados_dir, f'F1_Parametricos_{periodo}.csv'))

    # Reportes (versión resumida "Rep")
    if not descriptivo.empty:
        rep_desc_cols = ['variable','count','missing','missing_pct','mean','median','mode','min','p25','p50','p75','max','coef_var_pct','skew','kurtosis','metodo_sugerido_global']
        rep_desc = descriptivo[[c for c in rep_desc_cols if c in descriptivo.columns]].copy()
    else:
        rep_desc = pd.DataFrame()
    if not outliers.empty:
        rep_out = outliers[['variable','lower','upper','outliers','ratio']].copy()
    else:
        rep_out = pd.DataFrame()
    if not normalidad.empty:
        rep_norm = normalidad[['variable','n','skew','kurtosis','shapiro_p','approx_normal']].copy()
    else:
        rep_norm = pd.DataFrame()
    write_csv(rep_desc, os.path.join(reportes_dir, f'F1_Descriptivo_Rep_{periodo}.csv'))
    write_csv(rep_out, os.path.join(reportes_dir, f'F1_Outliers_Rep_{periodo}.csv'))
    write_csv(rep_norm, os.path.join(reportes_dir, f'F1_Normalidad_Rep_{periodo}.csv'))

    # Consolidado Global
    reporte = rep_desc.merge(rep_out, on='variable', how='left') if not rep_desc.empty else rep_out
    if not reporte.empty and not rep_norm.empty:
        reporte = reporte.merge(rep_norm[['variable','shapiro_p','approx_normal']], on='variable', how='left')
    write_csv(reporte, os.path.join(reportes_dir, f'Estadisticas_Global_{periodo}.csv'))

    log.info('Paso 7 completado (extendido)')
    return {
        'descriptivo': descriptivo.shape,
        'outliers': outliers.shape,
        'normalidad': normalidad.shape,
        'resultados': resultados.shape
    }

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Paso 7 Estadísticas Variables')
    parser.add_argument('--periodo', help='Periodo (ej: Sep25)', default=None)
    args = parser.parse_args()
    if args.periodo:
        per = args.periodo
    else:
        from datetime import datetime
        per = datetime.now().strftime('%b%y')
    log.info(f'Ejecutando Paso 7 para periodo {per}')
    run(per)