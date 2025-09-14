"""Paso 9: Separar por Colonias
Genera un CSV por colonia para cada combinación Ciudad-Operacion-Tipo, sólo si tiene >=5 propiedades.
Ruta: N1_Tratamiento/Consolidados/Colonias/<Ciudad>/<Venta|Renta>/<Tipo>/<Periodo>/
Nombre: Ciudad_Oper_Tipo_Periodo_ColXXXX.csv (Colonia abreviada a 7 chars)
Colonias con <5 propiedades se exportan a Esperando.
"""
from __future__ import annotations
import os, re, unicodedata
import pandas as pd
from esdata.utils.paths import (
    path_results_level, path_colonias_branch, path_esperando
)
from esdata.utils.io import read_csv, write_csv
from esdata.utils.logging_setup import get_logger

log = get_logger('step9')

def _slugify_colonia(nombre: str) -> str:
    if not isinstance(nombre,str):
        return 'COL'
    s = unicodedata.normalize('NFKD', nombre).encode('ascii','ignore').decode('ascii')
    s = re.sub(r'[^A-Za-z0-9]+','',s)
    return (s[:7] or 'COL').upper()

def _sanitize_token(token: str) -> str:
    if not isinstance(token, str):
        return 'NA'
    # Remover acentos y normalizar
    s = unicodedata.normalize('NFKD', token).encode('ascii','ignore').decode('ascii')
    # Reemplazar separadores problemáticos por guion bajo
    s = re.sub(r'[\\/]+','_', s)
    # Colapsar espacios y no alfanum
    s = re.sub(r'[^A-Za-z0-9]+','_', s)
    s = re.sub(r'_+','_', s).strip('_')
    return s or 'NA'

def run(periodo: str):
    base_num = os.path.join(path_results_level(1), f'0.Final_Num_{periodo}.csv')
    if not os.path.exists(base_num):
        raise FileNotFoundError(base_num)
    df = read_csv(base_num)
    req = {'Ciudad','operacion','tipo_propiedad','Colonia','id'}
    miss = req - set(df.columns)
    if miss:
        raise ValueError(f'Faltan columnas: {miss}')
    esperando_dir = path_esperando(periodo)
    combos = df[['Ciudad','operacion','tipo_propiedad']].drop_duplicates()
    for _, combo in combos.iterrows():
        ciudad = combo['Ciudad']; oper = combo['operacion']; tipo = combo['tipo_propiedad']
        ciudad_tok = _sanitize_token(ciudad)
        oper_tok = _sanitize_token(oper)
        tipo_tok = _sanitize_token(tipo)
        if ciudad_tok != ciudad or oper_tok != oper or tipo_tok != tipo:
            log.warning(f'Step9: tokens normalizados -> ciudad:"{ciudad}"=>"{ciudad_tok}" oper:"{oper}"=>"{oper_tok}" tipo:"{tipo}"=>"{tipo_tok}"')
        sub_combo = df[(df['Ciudad']==ciudad)&(df['operacion']==oper)&(df['tipo_propiedad']==tipo)]
        for colonia, sub_col in sub_combo.groupby('Colonia'):
            if len(sub_col) < 5:
                # Append to esperando (uno por combo acumulativo) usando tokens seguros
                write_csv(sub_col, os.path.join(esperando_dir, f'esperando_{ciudad_tok}_{oper_tok}_{tipo_tok}_{periodo}.csv'))
                continue
            abre = _slugify_colonia(colonia)
            # Usar tokens sanitizados para la ruta de carpetas (evita crear directorios inválidos)
            out_dir = path_colonias_branch(periodo, ciudad_tok, oper_tok, tipo_tok)
            out_name = f'{ciudad_tok}_{oper_tok}_{tipo_tok}_{periodo}_{abre}.csv'
            write_csv(sub_col, os.path.join(out_dir, out_name))
        log.info(f'Colonias separadas {ciudad_tok}-{oper_tok}-{tipo_tok}')
    log.info('Paso 9 completado')

if __name__=='__main__':
    from datetime import datetime
    per = datetime.now().strftime('%b%y')
    run(per)