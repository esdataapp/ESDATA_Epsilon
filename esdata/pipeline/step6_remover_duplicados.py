"""Paso 6: Remover Duplicados
Entradas: 5.Num_Corroborado, 4a, 4b
Salidas: 0.Final_Num, 0.Final_MKT, 0.Final_Ame + duplicados en Datos_Filtrados/Duplicados
"""
from __future__ import annotations
import os
import pandas as pd
from esdata.utils.io import read_csv, write_csv
from esdata.utils.paths import path_consolidados, path_base, ensure_dir, path_results_level
from esdata.utils.logging_setup import get_logger

log = get_logger('step6')


def _detect_duplicates(df):
    # Criterio: id ya debería ser único; si no, usar hash de (Ciudad, Colonia, precio, area_m2, tipo_propiedad)
    if df['id'].duplicated().any():
        df['__dup_key'] = df[['Ciudad','Colonia','precio','area_m2','tipo_propiedad']].astype(str).agg('|'.join, axis=1)
        dup_mask = df['__dup_key'].duplicated(keep='first')
    else:
        dup_mask = pd.Series([False]*len(df), index=df.index)
    return df[~dup_mask].copy(), df[dup_mask].copy()

ESSENTIAL_NUM_COLS = ["id","PaginaWeb","Ciudad","Colonia","operacion","tipo_propiedad","area_m2","recamaras","estacionamientos","precio","mantenimiento","longitud","latitud","tiempo_publicacion","Banos_totales","antiguedad_icon","PxM2"]

def _ensure_columns(df: pd.DataFrame, required: list[str]):
    for c in required:
        if c not in df.columns:
            df[c] = None
    return df

def run(periodo):
    base_dir = os.path.join(path_consolidados(), periodo)
    num_in = os.path.join(base_dir, f'5.Num_Corroborado_{periodo}.csv')
    tex_a = os.path.join(base_dir, f'4a.Tex_Titulo_Descripcion_{periodo}.csv')
    tex_b = os.path.join(base_dir, f'4b.Tex_Car_Ame_Ser_Ext_{periodo}.csv')
    for p in [num_in, tex_a, tex_b]:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
    num_df = read_csv(num_in)
    a_df = read_csv(tex_a)
    b_df = read_csv(tex_b)
    dedup_num, dupes = _detect_duplicates(num_df)
    # Guardar duplicados
    if len(dupes)>0:
        dup_dir = ensure_dir(path_base('Datos_Filtrados','Duplicados', periodo))
        write_csv(dupes, os.path.join(dup_dir, f'duplicados_{periodo}.csv'))
    # Filtrar marketing/amenidades segun ids finales
    ids_final = set(dedup_num['id'])
    a_final = a_df[a_df['id'].isin(ids_final)].copy()
    b_final = b_df[b_df['id'].isin(ids_final)].copy()
    # Reinyectar columnas faltantes 'operacion','mantenimiento','tipo_propiedad' si se perdieron en a_final o b_final desde num_df
    # Normalizar variantes de nombres antes de construir lookup
    variant_map = {
        'tiempo_publicacion dias': 'tiempo_publicacion',
        'antiguedad_años': 'antiguedad_icon',  # suponiendo que esta es la semántica usada posteriormente
        'Banos_totales': 'Banos_totales',
    }
    for old, new in variant_map.items():
        if old in num_df.columns and new not in num_df.columns:
            num_df.rename(columns={old: new}, inplace=True)
            if old in dedup_num.columns:
                dedup_num.rename(columns={old: new}, inplace=True)

    reinject_cols = ['operacion','mantenimiento','tipo_propiedad']
    # Usar dedup_num (ya libre de duplicados) como base de mapeo para evitar índice no único
    base_lookup = dedup_num.set_index('id')
    if not base_lookup.index.is_unique:
        # En caso extremo, mantener la primera aparición
        base_lookup = base_lookup[~base_lookup.index.duplicated(keep='first')]
    for col in reinject_cols:
        if col not in a_final.columns:
            a_final[col] = a_final['id'].map(base_lookup[col]) if col in base_lookup.columns else None
        if col not in b_final.columns:
            b_final[col] = b_final['id'].map(base_lookup[col]) if col in base_lookup.columns else None
    # Asegurar orden mínimo para marketing y amenidades (mantener demás columnas originales)
    a_final = _ensure_columns(a_final, ['id','PaginaWeb','Ciudad','Colonia','operacion','tipo_propiedad','area_m2','precio','mantenimiento'])
    b_final = _ensure_columns(b_final, ['id','Ciudad','Colonia','operacion','tipo_propiedad','area_m2','precio','mantenimiento'])
    # Agregar PxM2
    if 'precio' in dedup_num.columns and 'area_m2' in dedup_num.columns:
        mask = dedup_num['area_m2'].notna() & (dedup_num['area_m2']>0) & dedup_num['precio'].notna()
        dedup_num['PxM2'] = None
        dedup_num.loc[mask,'PxM2']= dedup_num.loc[mask,'precio']/dedup_num.loc[mask,'area_m2']
    for df, name in [(a_final,'MKT'),(b_final,'Ame')]:
        if 'precio' in df.columns and 'area_m2' in df.columns:
            mask2 = df['area_m2'].notna() & (df['area_m2']>0) & df['precio'].notna()
            df['PxM2']=None
            df.loc[mask2,'PxM2']= df.loc[mask2,'precio']/df.loc[mask2,'area_m2']
    # Salidas
    out_dir = ensure_dir(path_results_level(1))
    # Orden preferencial para archivo numérico
    dedup_num = _ensure_columns(dedup_num, ESSENTIAL_NUM_COLS)
    num_cols_order = [c for c in ESSENTIAL_NUM_COLS if c in dedup_num.columns] + [c for c in dedup_num.columns if c not in ESSENTIAL_NUM_COLS]
    dedup_num = dedup_num[num_cols_order]
    write_csv(dedup_num, os.path.join(out_dir, f'0.Final_Num_{periodo}.csv'))
    write_csv(a_final, os.path.join(out_dir, f'0.Final_MKT_{periodo}.csv'))
    write_csv(b_final, os.path.join(out_dir, f'0.Final_Ame_{periodo}.csv'))
    log.info(f'Registros finales: {len(dedup_num)} duplicados: {len(dupes)}')

if __name__=='__main__':
    from datetime import datetime
    per = datetime.now().strftime('%b%y')
    run(per)
