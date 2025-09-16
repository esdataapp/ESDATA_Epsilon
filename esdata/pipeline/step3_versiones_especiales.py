"""Paso 3: Versiones Especiales
Divide el consolidado con colonia en dos archivos Num y Tex sin eliminar propiedades.
Calcula PxM2 (precio por metro cuadrado) en la versión numérica.
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
from esdata.utils.io import read_csv, write_csv
from esdata.utils.paths import path_consolidados, ensure_dir
from esdata.utils.logging_setup import get_logger

log = get_logger('step3')

NUM_COLS = ["id","PaginaWeb","Ciudad","Fecha_Scrap","tipo_propiedad","area_m2","recamaras","estacionamientos","operacion","precio","mantenimiento","Colonia","longitud","latitud","tiempo_publicacion","Banos_totales","estacionamientos_icon","recamaras_icon","antiguedad_icon"]
TEX_COLS = ["id","PaginaWeb","Ciudad","Fecha_Scrap","tipo_propiedad","area_m2","recamaras","estacionamientos","operacion","precio","mantenimiento","Colonia","longitud","latitud","direccion","titulo","descripcion","anunciante","codigo_anunciante","codigo_inmuebles24","Caracteristicas_generales","Servicios","Amenidades","Exteriores"]

def calcular_pxm2(df):
    """Calcula precio por metro cuadrado (PxM2) de forma segura"""
    df['PxM2'] = np.nan
    
    # Validar que tenemos precio y area válidos
    mask_valido = (
        df['precio'].notna() & 
        df['area_m2'].notna() & 
        (df['precio'] > 0) & 
        (df['area_m2'] > 0)
    )
    
    # Calcular PxM2 solo para registros válidos
    df.loc[mask_valido, 'PxM2'] = df.loc[mask_valido, 'precio'] / df.loc[mask_valido, 'area_m2']
    
    valid_count = mask_valido.sum()
    total_count = len(df)
    
    log.info(f'PxM2 calculado para {valid_count:,} de {total_count:,} registros ({valid_count/total_count*100:.1f}%)')
    
    return df

def run(periodo):
    base_dir = os.path.join(path_consolidados(), periodo)
    inp = os.path.join(base_dir, f'2.Consolidado_ConColonia_{periodo}.csv')
    if not os.path.exists(inp):
        raise FileNotFoundError(inp)
        
    df = read_csv(inp)
    
    # Calcular PxM2 antes de dividir
    df = calcular_pxm2(df)
    
    # Agregar PxM2 a las columnas numéricas si no está ya
    num_cols_with_pxm2 = NUM_COLS + ['PxM2'] if 'PxM2' not in NUM_COLS else NUM_COLS
    
    df_num = df[[c for c in num_cols_with_pxm2 if c in df.columns]].copy()
    df_tex = df[[c for c in TEX_COLS if c in df.columns]].copy()
    
    write_csv(df_num, os.path.join(base_dir, f'3a.Consolidado_Num_{periodo}.csv'))
    write_csv(df_tex, os.path.join(base_dir, f'3b.Consolidado_Tex_{periodo}.csv'))
    
    log.info('Paso 3 completado con PxM2 calculado')

if __name__=='__main__':
    from datetime import datetime
    per = datetime.now().strftime('%b%y')
    run(per)
