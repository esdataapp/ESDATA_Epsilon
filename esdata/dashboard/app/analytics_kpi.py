"""Cálculo de KPIs ejecutivos para el dashboard.

compute_kpis(final_num, colony_stats, outliers, periodo, prev_periodo=None)
Devuelve dict con:
  n_propiedades
  precio_mediana
  PxM2_mediana
  PxM2_mediana_delta_pct (si periodo previo disponible)
  pct_outliers
  top_colonia_pxm2 (nombre)
  amenidades_promedio (si hay columnas amenidades binarias)
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
from esdata.utils.paths import path_base
from esdata.utils.io import read_csv


def _load_prev(periodo: str) -> str|None:
    """Intenta inferir periodo previo restando un mes al sufijo MonYY.
    No reimplementamos obtener_periodo_previo para evitar import circular pesada.
    """
    try:
        import datetime as _dt
        dt = _dt.datetime.strptime(periodo, '%b%y')
        month = dt.month - 1
        year = dt.year
        if month == 0:
            month = 12
            year -= 1
        prev = _dt.datetime(year, month, 1).strftime('%b%y')
        return prev
    except Exception:
        return None


def compute_kpis(final_num: pd.DataFrame, colony_stats: pd.DataFrame, outliers: pd.DataFrame,
                 periodo: str, prev_periodo: str|None=None) -> dict:
    kpis: dict[str, object] = {}
    # Total propiedades
    if final_num is not None and not final_num.empty:
        kpis['n_propiedades'] = int(final_num['id'].nunique() if 'id' in final_num.columns else len(final_num))
        # Medianas
        for var in ['precio','PxM2']:
            if var in final_num.columns and final_num[var].notna().any():
                kpis[f'{var}_mediana'] = float(np.median(final_num[var].dropna()))
    else:
        kpis['n_propiedades'] = 0

    # Precio m2 delta con periodo previo (si existe archivo previo en Dashboard)
    if prev_periodo is None:
        prev_periodo = _load_prev(periodo)
    if prev_periodo:
        prev_path = os.path.join(path_base('Dashboard','CSV', prev_periodo), 'colony_stats.csv')
        if os.path.exists(prev_path):
            try:
                prev_df = read_csv(prev_path)
                if 'PxM2_mediana' in prev_df.columns and 'PxM2_mediana' in colony_stats.columns:
                    curr = colony_stats['PxM2_mediana'].median()
                    prev = prev_df['PxM2_mediana'].median()
                    if prev and not pd.isna(prev) and prev!=0:
                        kpis['PxM2_mediana_delta_pct'] = float((curr - prev)/prev * 100)
                        kpis['PxM2_mediana_prev'] = float(prev)
            except Exception:
                pass

    # % outliers
    if outliers is not None and not outliers.empty and 'id' in outliers.columns:
        unique_out = int(outliers['id'].nunique())
        denom_raw = kpis.get('n_propiedades', 0)
        denom = int(denom_raw) if isinstance(denom_raw, (int,float)) else 0
        kpis['pct_outliers'] = float(unique_out/denom*100) if denom > 0 else 0.0

    # Top colonia por PxM2_actual
    if colony_stats is not None and not colony_stats.empty and 'PxM2_mediana' in colony_stats.columns:
        top_row = colony_stats.dropna(subset=['PxM2_mediana']).sort_values('PxM2_mediana', ascending=False).head(1)
        if not top_row.empty:
            kpis['top_colonia_pxm2'] = str(top_row.iloc[0]['Colonia'])
            kpis['top_colonia_pxm2_val'] = float(top_row.iloc[0]['PxM2_mediana'])

    # Amenidades promedio por propiedad (si dataset final_num trae columnas binarias amenidades)
    if final_num is not None and not final_num.empty:
        amen_cols = [c for c in final_num.columns if c.startswith('amen_') or c.startswith('serv_')]
        if amen_cols:
            sub = final_num[amen_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            kpis['amenidades_promedio'] = float(sub.sum(axis=1).mean())
            # Cobertura: % de amenidades con presencia > 5% (umbral configurable)
            thresh = 0.05
            presencias = (sub>0).mean(axis=0)
            if len(presencias)>0:
                kpis['amenidades_cobertura_pct'] = float((presencias >= thresh).mean()*100)
                kpis['amenidades_total'] = int(len(presencias))
                kpis['amenidades_significativas'] = int((presencias >= thresh).sum())

    return kpis
