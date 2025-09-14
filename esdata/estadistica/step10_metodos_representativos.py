"""Paso 10: Selección de Método Representativo (Media vs Mediana)

Extiende lógica incorporando evidencias de normalidad y variabilidad si existen
resultados previos del Paso 7 (coef_var_pct, shapiro_p, skew). Si no existen,
usa solo n y skew. Produce justificación textual.

Entrada base: 0.Final_Num_<Periodo>.csv
Entrada opcional: N2_Estadisticas/Reportes/<Periodo>/F1_Descriptivo_Rep_<Periodo>.csv
Salida: N5_Resultados/Nivel_1/CSV/Tablas/<Periodo>/metodos_representativos_<Periodo>.csv
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from esdata.utils.paths import path_results_level, path_resultados_tablas_periodo
from esdata.utils.io import read_csv, write_csv
from esdata.utils.logging_setup import get_logger

log = get_logger('step10')

VARS = ['precio','area_m2','PxM2']

def _ensure_pxm2(df: pd.DataFrame) -> pd.DataFrame:
    if 'PxM2' not in df.columns and {'precio','area_m2'} <= set(df.columns):
        mask = df['area_m2'].notna() & (df['area_m2']>0) & df['precio'].notna()
        df = df.copy()
        df['PxM2'] = np.nan
        df.loc[mask,'PxM2'] = df.loc[mask,'precio']/df.loc[mask,'area_m2']
    return df

def metodo_para(n: int, skew: float|None, shapiro_p: float|None, coef_var: float|None) -> tuple[str,str]:
    """Devuelve (metodo, justificacion)."""
    if n < 5:
        return 'no_estadistica', 'n<5 sin estadística confiable'
    if n < 10:
        return 'mediana_rango', '5<=n<10 usar mediana+rango'
    # Normalidad y estabilidad
    normal = False
    if shapiro_p is not None and not pd.isna(shapiro_p):
        normal = shapiro_p > 0.05
    # Fallback normalidad aproximada por skew
    if skew is not None and not pd.isna(skew):
        if abs(skew) <= 0.5:
            normal = normal or True  # si skew bajo, consideramos cercano a normal
    # Variabilidad razonable (coef_var_pct < 100%) si disponible
    var_estable = True if coef_var is None or pd.isna(coef_var) else coef_var < 100
    if normal and n>=30 and var_estable:
        return 'media_desv', 'n>=30 & normalidad aceptada'
    if skew is not None and not pd.isna(skew) and abs(skew) > 1:
        return 'mediana_IQR', 'asimetría fuerte |skew|>1'
    if n>=30 and normal:
        return 'media_desv', 'n>=30 & normalidad (skew bajo)'
    return 'mediana_IQR', 'condiciones mixtas: preferible robustez'

def run(periodo: str):
    base_num = os.path.join(path_results_level(1), f'0.Final_Num_{periodo}.csv')
    if not os.path.exists(base_num):
        raise FileNotFoundError(base_num)
    df = read_csv(base_num)
    df = _ensure_pxm2(df)
    needed = {'Ciudad','operacion','tipo_propiedad','Colonia'}
    if not needed.issubset(df.columns):
        raise ValueError('Faltan columnas para agrupacion')

    # Intentar cargar reporte descriptivo para extraer coef_var_pct, skew, shapiro_p
    rep_desc_path = os.path.join('N2_Estadisticas','Reportes', periodo, f'F1_Descriptivo_Rep_{periodo}.csv')
    rep_norm_path = os.path.join('N2_Estadisticas','Reportes', periodo, f'F1_Normalidad_Rep_{periodo}.csv')
    aux_desc = None; aux_norm = None
    if os.path.exists(rep_desc_path):
        try:
            aux_desc = pd.read_csv(rep_desc_path, encoding='utf-8')
        except Exception:
            aux_desc = None
    if os.path.exists(rep_norm_path):
        try:
            aux_norm = pd.read_csv(rep_norm_path, encoding='utf-8')
        except Exception:
            aux_norm = None

    rows=[]
    for (ciudad, oper, tipo, colonia), sub in df.groupby(['Ciudad','operacion','tipo_propiedad','Colonia']):
        n = len(sub)
        row_base = {
            'Periodo': periodo,
            'Ciudad': ciudad,
            'Operacion': oper,
            'Tipo': tipo,
            'Colonia': colonia,
            'n': n
        }
        for v in VARS:
            if v not in sub.columns:
                continue
            serie = sub[v].dropna().astype(float)
            skew = pd.to_numeric(pd.Series([serie.skew()]), errors='coerce').iloc[0] if len(serie)>2 else None
            # Buscar métricas globales si existen
            coef_var = None; shapiro_p = None
            if aux_desc is not None and 'variable' in aux_desc.columns and 'coef_var_pct' in aux_desc.columns:
                try:
                    coef_var = aux_desc.loc[aux_desc['variable']==v,'coef_var_pct'].iloc[0]
                except Exception:
                    pass
            if aux_norm is not None and 'variable' in aux_norm.columns and 'shapiro_p' in aux_norm.columns:
                try:
                    shapiro_p = aux_norm.loc[aux_norm['variable']==v,'shapiro_p'].iloc[0]
                except Exception:
                    pass
            metodo, just = metodo_para(n, skew, shapiro_p, coef_var)
            if metodo == 'no_estadistica':
                rep = None
            elif metodo.startswith('media'):
                rep = serie.mean() if not serie.empty else None
            else:
                rep = serie.median() if not serie.empty else None
            row_base[f'{v}_metodo']=metodo
            row_base[f'{v}_representativo']=rep
            row_base[f'{v}_skew']=skew
            row_base[f'{v}_shapiro_p']=shapiro_p
            row_base[f'{v}_coef_var_pct']=coef_var
            row_base[f'{v}_justificacion']=just
        rows.append(row_base.copy())
    out_df = pd.DataFrame(rows)
    out_dir = path_resultados_tablas_periodo(periodo)
    write_csv(out_df, os.path.join(out_dir, f'metodos_representativos_{periodo}.csv'))
    log.info('Paso 10 completado')

if __name__=='__main__':
    from datetime import datetime
    per = datetime.now().strftime('%b%y')
    run(per)