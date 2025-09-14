"""Generador de CSV para Dashboard Ultra Inmobiliario

Este módulo produce múltiples datasets analíticos a partir de:
 - 0.Final_Num_<periodo>.csv (base numérica depurada)
 - 0.Final_Ame_<periodo>.csv (amenidades por propiedad)
 - 0.Final_MKT_<periodo>.csv (marketing / texto enriquecido)

Salidas (carpeta Dashboard/CSV/<periodo>/):
 1. colony_stats.csv -> Métricas por Ciudad/Colonia/operacion/tipo_propiedad
 2. colony_quantiles.csv -> Quantiles extendidos y medidas robustas
 3. colony_distribution_long.csv -> Distribución larga (para boxplots, violin)
 4. price_area_heatmap_matrix.csv -> Matriz de estratos area_m2 x precio (conteos y medianas PxM2)
 5. amenity_prevalence.csv -> Prevalencia de amenidades por colonia (freq y ratio)
 6. marketing_signals.csv -> Resumen de variables marketing agregadas por colonia
 7. outliers_flagged.csv -> Registro de outliers detectados con métodos IQR y Z-score
 8. pxm2_evolution_stub.csv -> Plantilla para análisis temporal (si hay históricos)

Uso CLI:
    python -m esdata.dashboard.generate_dashboard_data Sep25
"""
from __future__ import annotations
import os, math, sys

# Fallback para permitir ejecución directa (python generate_dashboard_data.py <Periodo>)
_CURR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_CURR, '..', '..'))  # carpeta que contiene paquete esdata
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import pandas as pd
import numpy as np
try:
    from esdata.utils.paths import path_results_level, ensure_dir, path_base, path_resultados_tablas_periodo
    from esdata.utils.io import read_csv, write_csv
    from esdata.utils.logging_setup import get_logger
except ModuleNotFoundError as e:  # Mensaje amigable
    raise SystemExit('No se pudo importar paquete esdata. Ejecuta desde la raíz: python -m esdata.dashboard.generate_dashboard_data <Periodo>') from e

log = get_logger('dashboard')

NUM_COL_REQUIRED = ["id","Ciudad","Colonia","operacion","tipo_propiedad","area_m2","precio","PxM2"]
AMENITY_PREFIXES = []  # se autodeducen (amenidades canónicas) excluyendo meta
MKT_PREFIX_DESC = 'desc_'
MKT_PREFIX_TIT = 'titulo_'

# Estratos configurables
AREA_BINS = [0,50,80,120,180,250,400,600,1000,10_000]
PRICE_BINS = [0,1_000_000,2_000_000,3_000_000,5_000_000,7_500_000,10_000_000,15_000_000,25_000_000,100_000_000]

QUANTILES = [0.05,0.10,0.25,0.5,0.75,0.9,0.95]


def _load(periodo: str):
    base_dir = path_results_level(1)
    num_path = os.path.join(base_dir, f'0.Final_Num_{periodo}.csv')
    ame_path = os.path.join(base_dir, f'0.Final_Ame_{periodo}.csv')
    mkt_path = os.path.join(base_dir, f'0.Final_MKT_{periodo}.csv')
    for p in [num_path, ame_path, mkt_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
    num = read_csv(num_path)
    ame = read_csv(ame_path)
    mkt = read_csv(mkt_path)
    return num, ame, mkt


def _prepare_numeric(num: pd.DataFrame) -> pd.DataFrame:
    df = num.copy()
    if 'PxM2' not in df.columns and {'precio','area_m2'} <= set(df.columns):
        mask = df['area_m2'].notna() & (df['area_m2']>0) & df['precio'].notna()
        df['PxM2'] = None
        df.loc[mask,'PxM2'] = df.loc[mask,'precio']/df.loc[mask,'area_m2']
    return df


def _derive_strata(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['estrato_area'] = pd.cut(df['area_m2'], AREA_BINS, right=False, include_lowest=True)
    df['estrato_precio'] = pd.cut(df['precio'], PRICE_BINS, right=False, include_lowest=True)
    return df


def _colony_group_keys(df: pd.DataFrame):
    keys = ['Ciudad','Colonia','operacion','tipo_propiedad']
    return [k for k in keys if k in df.columns]


def _safe_agg(series, func):
    try:
        return func(series.dropna()) if len(series.dropna())>0 else np.nan
    except Exception:
        return np.nan


def build_colony_stats(df: pd.DataFrame) -> pd.DataFrame:
    keys = _colony_group_keys(df)
    metrics: list[dict[str, object]] = []
    grp = df.groupby(keys, dropna=False)
    for gk, sub in grp:
        row: dict[str, object] = {k:v for k,v in zip(keys, gk if isinstance(gk, tuple) else (gk,))}
        row['n_propiedades'] = len(sub)
        for var in ['precio','area_m2','PxM2']:
            if var in sub.columns:
                s = sub[var]
                row[f'{var}_min'] = _safe_agg(s, np.min)  # type: ignore
                row[f'{var}_mediana'] = _safe_agg(s, np.median)  # type: ignore
                row[f'{var}_media'] = _safe_agg(s, np.mean)  # type: ignore
                row[f'{var}_max'] = _safe_agg(s, np.max)  # type: ignore
                row[f'{var}_std'] = _safe_agg(s, np.std)  # type: ignore
                row[f'{var}_iqr'] = _safe_agg(s, lambda x: np.percentile(x,75)-np.percentile(x,25) if len(x)>0 else np.nan)  # type: ignore
                row[f'{var}_skew_aprox'] = _safe_agg(s, lambda x: ( (x.mean()-np.median(x))/ (x.std()+1e-9) ) if x.std()>0 else 0)  # type: ignore
        # Rango precio y area
        if 'precio_min' in row and 'precio_max' in row:
            try:  # type: ignore
                pmin = pd.to_numeric(pd.Series([row['precio_min']]), errors='coerce').iloc[0]
                pmax = pd.to_numeric(pd.Series([row['precio_max']]), errors='coerce').iloc[0]
                row['precio_rango'] = pmax - pmin if pd.notna(pmin) and pd.notna(pmax) else np.nan
            except Exception:
                row['precio_rango'] = np.nan
        if 'area_m2_min' in row and 'area_m2_max' in row:
            try:  # type: ignore
                amin = pd.to_numeric(pd.Series([row['area_m2_min']]), errors='coerce').iloc[0]
                amax = pd.to_numeric(pd.Series([row['area_m2_max']]), errors='coerce').iloc[0]
                row['area_m2_rango'] = amax - amin if pd.notna(amin) and pd.notna(amax) else np.nan
            except Exception:
                row['area_m2_rango'] = np.nan
        # Recamaras
        if 'recamaras' in sub.columns:
            s = sub['recamaras'].dropna()
            if len(s)>0:
                row['recamaras_min'] = float(s.min())
                row['recamaras_media'] = float(s.mean())
                row['recamaras_max'] = float(s.max())
        # Estacionamientos
        if 'estacionamientos' in sub.columns:
            s = sub['estacionamientos'].dropna()
            if len(s)>0:
                row['estacionamientos_min'] = float(s.min())
                row['estacionamientos_media'] = float(s.mean())
                row['estacionamientos_max'] = float(s.max())
        # Mantenimiento promedio
        if 'mantenimiento' in sub.columns and sub['mantenimiento'].notna().any():
            row['mantenimiento_media'] = float(sub['mantenimiento'].dropna().mean())
        # (clasificación se calcula después del loop)
        metrics.append(row)
    result = pd.DataFrame(metrics)
    # Clasificación Premium/Medio/Económico por terciles de mediana PxM2 dentro de cada (Ciudad, operacion, tipo_propiedad)
    if 'PxM2_mediana' in result.columns:
        group_class = result.groupby([c for c in ['Ciudad','operacion','tipo_propiedad'] if c in result.columns])
        labels=[]
        for _, sub in group_class:
            med = sub['PxM2_mediana']
            if med.notna().sum()<3:
                # fallback simple: todo Medio
                cat = ['Medio']*len(sub)
            else:
                q1 = med.quantile(1/3)
                q2 = med.quantile(2/3)
                cat=[]
                for v in med:
                    if pd.isna(v):
                        cat.append(None)
                    elif v<=q1:
                        cat.append('Económico')
                    elif v>=q2:
                        cat.append('Premium')
                    else:
                        cat.append('Medio')
            labels.extend(cat)
        result['clasificacion_mercado'] = labels
    return result


def build_colony_quantiles(df: pd.DataFrame) -> pd.DataFrame:
    keys = _colony_group_keys(df)
    rows=[]
    for gk, sub in df.groupby(keys, dropna=False):
        base = {k:v for k,v in zip(keys, gk if isinstance(gk, tuple) else (gk,))}
        for var in ['precio','area_m2','PxM2']:
            if var in sub.columns and sub[var].notna().any():
                vals = sub[var].dropna()
                for q in QUANTILES:
                    base[f'{var}_q{int(q*100)}'] = float(np.quantile(vals, q))  # type: ignore
        rows.append(base.copy())
    return pd.DataFrame(rows)


def build_distribution_long(df: pd.DataFrame) -> pd.DataFrame:
    keys = _colony_group_keys(df)
    keep = keys + ['precio','area_m2','PxM2']
    data = df[keep].melt(id_vars=keys, var_name='variable', value_name='valor')
    return data


def build_heatmap_matrix(df: pd.DataFrame) -> pd.DataFrame:
    # Conteo de propiedades
    count_tbl = df.pivot_table(index='estrato_area', columns='estrato_precio', values='id', aggfunc='count', fill_value=0, dropna=False)
    # Mediana PxM2 por celda
    median_tbl = df.pivot_table(index='estrato_area', columns='estrato_precio', values='PxM2', aggfunc='median', dropna=False)
    # Sufijos para diferenciar
    count_tbl = count_tbl.add_prefix('n_')
    median_tbl = median_tbl.add_prefix('med_PxM2_')
    wide = pd.concat([count_tbl, median_tbl], axis=1)
    # Totales por fila (solo conteo)
    wide['n_TOTAL_FILA'] = wide[[c for c in wide.columns if c.startswith('n_') and c!='n_TOTAL_FILA']].sum(axis=1)
    # Totales por columna (solo conteo)
    count_total_col = wide[[c for c in wide.columns if c.startswith('n_') and c!='n_TOTAL_FILA']].sum(axis=0)
    total_row = pd.DataFrame([count_total_col], index=['TOTAL_COLUMNA'])
    wide = pd.concat([wide, total_row])
    return wide.reset_index()

def build_heatmap_long(df: pd.DataFrame) -> pd.DataFrame:
    # Generar formato largo con conteo y mediana PxM2 por par de estratos
    grp = df.groupby(['estrato_area','estrato_precio'], dropna=False)
    rows=[]
    for (ea, ep), sub in grp:
        rows.append({
            'estrato_area': ea,
            'estrato_precio': ep,
            'n': len(sub),
            'mediana_PxM2': float(sub['PxM2'].median()) if 'PxM2' in sub.columns and sub['PxM2'].notna().any() else np.nan
        })
    return pd.DataFrame(rows)


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    records=[]
    for var in ['precio','area_m2','PxM2']:
        if var not in df.columns: continue
        series = df[var].dropna()
        if len(series)<5: continue
        q1,q3 = np.percentile(series,25), np.percentile(series,75)
        iqr = q3-q1
        low, high = q1-1.5*iqr, q3+1.5*iqr
        mean, std = series.mean(), series.std()
        for idx,row in df.loc[df[var].notna()].iterrows():
            val=row[var]
            flag_iqr = int(val<low or val>high)
            flag_z = int(std>0 and abs((val-mean)/std)>3)
            if flag_iqr or flag_z:
                records.append({'id':row['id'],'variable':var,'valor':val,'flag_iqr':flag_iqr,'flag_zscore':flag_z,'low_iqr':low,'high_iqr':high})
    return pd.DataFrame(records)


def amenity_prevalence(df_ame: pd.DataFrame, ids_final: set) -> pd.DataFrame:
    meta = ['id','Ciudad','Colonia','operacion','tipo_propiedad']
    amen_cols = [c for c in df_ame.columns if c not in meta and c not in ('PaginaWeb','Fecha_Scrap','area_m2','precio','mantenimiento')]
    sub = df_ame[df_ame['id'].isin(ids_final)].copy()
    long_rows=[]
    for col in amen_cols:
        present = sub[col].fillna(0)
        # consider >0 as present
        ratio = (present>0).mean()
        long_rows.append({'amenidad':col,'n_propiedades':len(sub),'ratio_presencia':ratio,'conteo_presencia':int((present>0).sum())})
    return pd.DataFrame(long_rows)


def marketing_signals(mkt: pd.DataFrame, ids_final: set) -> pd.DataFrame:
    sub = mkt[mkt['id'].isin(ids_final)]
    desc_cols = [c for c in sub.columns if c.startswith(MKT_PREFIX_DESC)]
    tit_cols = [c for c in sub.columns if c.startswith(MKT_PREFIX_TIT)]
    rows=[]
    total = len(sub)
    for col in desc_cols+tit_cols:
        s = sub[col]
        if s.dropna().dtype!='O':
            # assumed numeric / binary
            rows.append({'variable':col,'tasa': s.fillna(0).mean(), 'conteo': int((s.fillna(0)>0).sum()),'n_total': total})
    return pd.DataFrame(rows)


def pxm2_evolution_stub(df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    # Placeholder para futuros históricos.
    out = df[['Ciudad','Colonia','operacion','tipo_propiedad','PxM2']].groupby(['Ciudad','Colonia','operacion','tipo_propiedad']).agg(PxM2_median=('PxM2','median')).reset_index()
    out['periodo']=periodo
    return out


def _load_metodos(periodo: str) -> pd.DataFrame|None:
    try:
        tablas_dir = path_resultados_tablas_periodo(periodo)
        path_met = os.path.join(tablas_dir, f'metodos_representativos_{periodo}.csv')
        if os.path.exists(path_met):
            return read_csv(path_met)
    except Exception as e:
        log.warning(f'No se pudo cargar metodos representativos: {e}')
    return None

def run(periodo: str):
    num, ame, mkt = _load(periodo)
    num = _prepare_numeric(num)
    num = _derive_strata(num)
    ids_final = set(num['id'])
    out_dir = ensure_dir(path_base('Dashboard','CSV', periodo))

    # 1 colony stats
    colony_stats = build_colony_stats(num)
    # Enriquecer con métodos representativos si existen
    metodos = _load_metodos(periodo)
    if metodos is not None:
        # Simplificar a columnas de representativo por variable
        keep_cols = ['Ciudad','Operacion','Tipo','Colonia']
        value_cols = []
        for v in ['precio','area_m2','PxM2']:
            for suf in ['metodo','representativo']:
                col = f'{v}_{suf}'
                if col in metodos.columns:
                    value_cols.append(col)
        merge_df = metodos[keep_cols + value_cols].copy() if all(c in metodos.columns for c in keep_cols) else None
        if merge_df is not None:
            # Normalizar naming en colony_stats (operacion/tipo_propiedad vs Operacion/Tipo)
            if 'operacion' in colony_stats.columns:
                merge_df = merge_df.rename(columns={'Operacion':'operacion'})
            if 'tipo_propiedad' in colony_stats.columns:
                merge_df = merge_df.rename(columns={'Tipo':'tipo_propiedad'})
            colony_stats = colony_stats.merge(merge_df, on=['Ciudad','Colonia','operacion','tipo_propiedad'], how='left')
    write_csv(colony_stats, os.path.join(out_dir,'colony_stats.csv'))

    # 2 quantiles
    colony_q = build_colony_quantiles(num)
    write_csv(colony_q, os.path.join(out_dir,'colony_quantiles.csv'))

    # 3 distribution long
    dist_long = build_distribution_long(num)
    write_csv(dist_long, os.path.join(out_dir,'colony_distribution_long.csv'))

    # 4 heatmap matrix
    heat = build_heatmap_matrix(num)
    write_csv(heat, os.path.join(out_dir,'price_area_heatmap_matrix.csv'))
    heat_long = build_heatmap_long(num)
    write_csv(heat_long, os.path.join(out_dir,'price_area_heatmap_long.csv'))

    # 5 amenity prevalence
    ame_prev = amenity_prevalence(ame, ids_final)
    write_csv(ame_prev, os.path.join(out_dir,'amenity_prevalence.csv'))

    # 6 marketing signals
    try:
        mkt_sig = marketing_signals(mkt, ids_final)
        write_csv(mkt_sig, os.path.join(out_dir,'marketing_signals.csv'))
    except Exception as e:
        log.warning(f'Marketing signals falló: {e}')

    # 7 outliers
    outliers = detect_outliers(num)
    write_csv(outliers, os.path.join(out_dir,'outliers_flagged.csv'))

    # 8 pxm2 evolution stub
    evol = pxm2_evolution_stub(num, periodo)
    write_csv(evol, os.path.join(out_dir,'pxm2_evolution_stub.csv'))

    log.info('Dashboard CSV generados')

if __name__ == '__main__':
    import sys
    if len(sys.argv)<2:
        raise SystemExit('Uso: python -m esdata.dashboard.generate_dashboard_data <PeriodoEj: Sep25>')
    run(sys.argv[1])
