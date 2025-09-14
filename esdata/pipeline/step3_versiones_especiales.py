"""Paso 3: Versiones Especiales
Divide el consolidado con colonia en dos archivos Num y Tex sin eliminar propiedades.
"""
from __future__ import annotations
import os
import pandas as pd
from esdata.utils.io import read_csv, write_csv
from esdata.utils.paths import path_consolidados, ensure_dir
from esdata.utils.logging_setup import get_logger

log = get_logger('step3')

NUM_COLS = ["id","PaginaWeb","Ciudad","Fecha_Scrap","tipo_propiedad","area_m2","recamaras","estacionamientos","operacion","precio","mantenimiento","Colonia","longitud","latitud","tiempo_publicacion","Banos_totales","estacionamientos_icon","recamaras_icon","antiguedad_icon"]
TEX_COLS = ["id","PaginaWeb","Ciudad","Fecha_Scrap","tipo_propiedad","area_m2","recamaras","estacionamientos","operacion","precio","mantenimiento","Colonia","longitud","latitud","direccion","titulo","descripcion","anunciante","codigo_anunciante","codigo_inmuebles24","Caracteristicas_generales","Servicios","Amenidades","Exteriores"]

def run(periodo):
    base_dir = os.path.join(path_consolidados(), periodo)
    inp = os.path.join(base_dir, f'2.Consolidado_ConColonia_{periodo}.csv')
    if not os.path.exists(inp):
        raise FileNotFoundError(inp)
    df = read_csv(inp)
    df_num = df[[c for c in NUM_COLS if c in df.columns]].copy()
    df_tex = df[[c for c in TEX_COLS if c in df.columns]].copy()
    write_csv(df_num, os.path.join(base_dir, f'3a.Consolidado_Num_{periodo}.csv'))
    write_csv(df_tex, os.path.join(base_dir, f'3b.Consolidado_Tex_{periodo}.csv'))
    log.info('Paso 3 completado')

if __name__=='__main__':
    from datetime import datetime
    per = datetime.now().strftime('%b%y')
    run(per)
