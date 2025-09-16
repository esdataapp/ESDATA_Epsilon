"""Paso 5: Análisis Lógico y Corroboración (Mejorado)

Combina 3a (num) + 4a (texto) para validar y corregir.
Incluye filtros lógicos avanzados multi-sensibilidad inspirados en script optimizado.

Salidas:
    - 5.Num_Corroborado_<Periodo>.csv (registros válidos)
    - Datos_Filtrados/Eliminados/<Periodo>/paso5_invalidos_<Periodo>.csv (registros irreparables con motivos)

Se calculan razones de eliminación y se documentan para auditoría.
"""
from __future__ import annotations
import os, sys, argparse
import pandas as pd
import numpy as np
from esdata.utils.io import read_csv, write_csv
from esdata.utils.paths import path_consolidados, path_base, ensure_dir
from esdata.utils.logging_setup import get_logger

log = get_logger('step5')

NUM_KEEP_COLS = [
    "id","PaginaWeb","Ciudad","Fecha_Scrap","tipo_propiedad","area_m2","recamaras","estacionamientos",
    "operacion","precio","mantenimiento","Colonia","longitud","latitud","tiempo_publicacion","Banos_totales",
    "antiguedad_icon","PxM2"
]

SENSITIVITY_THRESHOLDS = {
    'ultra_conservadora': {
        'area_min': 20,'area_max_depto':1200,'area_max_casa':6000,
        'precio_min_depto':200000,'precio_max_depto':80000000,
        'precio_min_casa':300000,'precio_max_casa':120000000,
        'pxm2_max':250000,'rec_max_depto':6,'rec_max_casa':12,
        'banos_ratio_max':3.0,'estac_ratio_max':2.5,'area_min_por_rec':12
    },
    'conservadora': {
        'area_min':25,'area_max_depto':1000,'area_max_casa':5000,
        'precio_min_depto':300000,'precio_max_depto':60000000,
        'precio_min_casa':400000,'precio_max_casa':80000000,
        'pxm2_max':200000,'rec_max_depto':5,'rec_max_casa':10,
        'banos_ratio_max':2.5,'estac_ratio_max':2.0,'area_min_por_rec':15
    },
    'normal': {
        'area_min':30,'area_max_depto':800,'area_max_casa':3000,
        'precio_min_depto':400000,'precio_max_depto':50000000,
        'precio_min_casa':500000,'precio_max_casa':60000000,
        'pxm2_max':150000,'rec_max_depto':5,'rec_max_casa':8,
        'banos_ratio_max':2.0,'estac_ratio_max':1.5,'area_min_por_rec':18
    },
    'estricta': {
        'area_min':35,'area_max_depto':600,'area_max_casa':2500,
        'precio_min_depto':500000,'precio_max_depto':40000000,
        'precio_min_casa':600000,'precio_max_casa':50000000,
        'pxm2_max':120000,'rec_max_depto':4,'rec_max_casa':7,
        'banos_ratio_max':1.8,'estac_ratio_max':1.2,'area_min_por_rec':20
    }
}


def _merge(num_df, texto_df):
    if 'id' not in num_df.columns or 'id' not in texto_df.columns:
        return num_df
    # Garantizar unicidad en texto_df (puede venir duplicado por errores previos)
    tex_sub = texto_df[['id','recamaras_texto','banos_texto']].copy()
    # Si hay duplicados de id, priorizar filas con más información (no nulos)
    if tex_sub['id'].duplicated().any():
        tex_sub['__info_score'] = tex_sub[['recamaras_texto','banos_texto']].notna().sum(axis=1)
        tex_sub = tex_sub.sort_values('__info_score', ascending=False).drop_duplicates('id', keep='first').drop(columns='__info_score')
    return num_df.merge(tex_sub, on='id', how='left')

def _improve(df):
    # Reemplazar recamaras/banos si faltan
    if 'recamaras_texto' in df.columns:
        mask = (df['recamaras'].isna() | (df['recamaras']<=0)) & df['recamaras_texto'].notna()
        df.loc[mask,'recamaras']=df.loc[mask,'recamaras_texto']
    if 'banos_texto' in df.columns and 'Banos_totales' in df.columns:
        mask2 = (df['Banos_totales'].isna() | (df['Banos_totales']<=0)) & df['banos_texto'].notna()
        df.loc[mask2,'Banos_totales']=df.loc[mask2,'banos_texto']
    return df

def _compute_pxm2(df: pd.DataFrame):
    if 'PxM2' not in df.columns:
        df['PxM2']=np.nan
    mask = df['area_m2'].notna() & (df['area_m2']>0) & df['precio'].notna() & (df['precio']>0)
    df.loc[mask,'PxM2']= df.loc[mask,'precio']/df.loc[mask,'area_m2']
    return df

def _logic_filter(df: pd.DataFrame, sensibilidad: str):
    thr = SENSITIVITY_THRESHOLDS[sensibilidad]
    motivos = []
    keep_idx = []
    drop_rows = []
    for idx, row in df.iterrows():
        row_motivos = []
        precio = row.get('precio')
        area = row.get('area_m2')
        tipo = str(row.get('tipo_propiedad','')).lower()
        rec = row.get('recamaras')
        banos = row.get('Banos_totales') if 'Banos_totales' in df.columns else row.get('banos')
        estac = row.get('estacionamientos')
        pxm2 = row.get('PxM2')

        # básicos
        if pd.isna(precio) or precio<=0: row_motivos.append('precio<=0')
        if pd.isna(area) or area<=0: row_motivos.append('area<=0')
        if pd.isna(rec) or rec<=0: row_motivos.append('recamaras_invalidas')
        if pd.isna(banos) or banos<=0: row_motivos.append('banos_invalidos')

        # tipo thresholds
        if not row_motivos:
            es_depto = any(x in tipo for x in ['dep','depart'])
            if es_depto:
                if area < thr['area_min'] or area > thr['area_max_depto']: row_motivos.append('area_fuera_rango_depto')
                if precio < thr['precio_min_depto'] or precio > thr['precio_max_depto']: row_motivos.append('precio_fuera_rango_depto')
                if rec > thr['rec_max_depto']: row_motivos.append('recamaras_excesivas_depto')
            else:
                if area < thr['area_min'] or area > thr['area_max_casa']: row_motivos.append('area_fuera_rango_casa')
                if precio < thr['precio_min_casa'] or precio > thr['precio_max_casa']: row_motivos.append('precio_fuera_rango_casa')
                if rec > thr['rec_max_casa']: row_motivos.append('recamaras_excesivas_casa')

            # ratios (con validación de división por cero)
            if pd.notna(banos) and pd.notna(rec) and rec > 0:
                ratio_b = banos / rec
                if ratio_b > thr['banos_ratio_max']: 
                    row_motivos.append('ratio_banos_rec_excesivo')
            if pd.notna(estac) and pd.notna(rec) and rec > 0 and estac > 0:
                ratio_e = estac / rec
                if ratio_e > thr['estac_ratio_max']: 
                    row_motivos.append('ratio_estac_rec_excesivo')
            if pd.notna(area) and pd.notna(rec) and rec > 0 and area > 0:
                area_por_rec = area / rec
                if area_por_rec < thr['area_min_por_rec']: 
                    row_motivos.append('area_por_rec_baja')

            if pd.notna(pxm2) and pxm2>thr['pxm2_max']:
                row_motivos.append('PxM2_excesivo')

        if row_motivos:
            drop_rows.append(idx)
            motivos.append((idx,';'.join(row_motivos)))
        else:
            keep_idx.append(idx)

    valid = df.loc[keep_idx].copy()
    invalid = df.loc[drop_rows].copy()
    if len(motivos)>0:
        invalid['motivos_eliminacion'] = [m[1] for m in motivos]
    return valid, invalid

def run(periodo, sensibilidad='conservadora'):
    base_dir = os.path.join(path_consolidados(), periodo)
    num_path = os.path.join(base_dir, f'3a.Consolidado_Num_{periodo}.csv')
    tex_num_path = os.path.join(base_dir, f'4a.Tex_Titulo_Descripcion_{periodo}.csv')
    if not os.path.exists(num_path) or not os.path.exists(tex_num_path):
        raise FileNotFoundError('Faltan entradas para paso 5')
    num_df = read_csv(num_path)
    tex_df = read_csv(tex_num_path)
    merged = _merge(num_df, tex_df)
    improved = _improve(merged)
    improved = _compute_pxm2(improved)
    if sensibilidad not in SENSITIVITY_THRESHOLDS:
        log.warning(f"Sensibilidad {sensibilidad} no reconocida; usando 'conservadora'")
        sensibilidad = 'conservadora'
    valid, invalid = _logic_filter(improved, sensibilidad)
    out_valid = valid[[c for c in NUM_KEEP_COLS if c in valid.columns]].copy()
    write_csv(out_valid, os.path.join(base_dir, f'5.Num_Corroborado_{periodo}.csv'))
    if len(invalid)>0:
        elim_dir = ensure_dir(path_base('Datos_Filtrados','Eliminados', periodo))
        write_csv(invalid, os.path.join(elim_dir, f'paso5_invalidos_{periodo}.csv'))
    log.info(f'Validos {len(valid)} Invalidos {len(invalid)} Sensibilidad {sensibilidad}')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Paso 5 Analisis Logico Corroboracion Mejorado')
    parser.add_argument('--periodo', help='Periodo (ej Sep25)', default=None)
    parser.add_argument('--sensibilidad', help='ultra_conservadora|conservadora|normal|estricta', default='conservadora')
    args = parser.parse_args()
    if args.periodo:
        per = args.periodo
    else:
        from datetime import datetime
        per = datetime.now().strftime('%b%y')
    run(per, args.sensibilidad)
