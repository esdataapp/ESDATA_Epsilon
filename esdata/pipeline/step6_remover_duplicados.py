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
    """Jerarquía para buscar duplicados:
    1. Si misma area_m2 -> revisar Ciudad
    2. Si Ciudad duplicada -> revisar Colonia  
    3. Si Colonia duplicada -> revisar precio
    4. Si precio duplicado -> revisar longitud
    5. Si longitud duplicada -> revisar latitud
    6. Solo si todo es igual -> revisar recamaras y banos
    """
    
    # Crear DataFrame de trabajo con copias de las columnas
    work_df = df.copy()
    
    # Normalizar valores nulos para comparación
    for col in ['area_m2', 'Ciudad', 'Colonia', 'precio', 'longitud', 'latitud', 'recamaras', 'Banos_totales', 'banos_icon']:
        if col in work_df.columns:
            work_df[col] = work_df[col].fillna('NULL_VALUE')
    
    # Aplicar jerarquía de detección
    duplicates_mask = pd.Series([False] * len(work_df), index=work_df.index)
    
    # Agrupar por area_m2
    area_groups = work_df.groupby('area_m2')
    
    for area_val, area_group in area_groups:
        if len(area_group) <= 1:
            continue  # No hay duplicados posibles en este grupo
            
        # Revisar Ciudad dentro del grupo de área
        ciudad_groups = area_group.groupby('Ciudad')
        
        for ciudad_val, ciudad_group in ciudad_groups:
            if len(ciudad_group) <= 1:
                continue
                
            # Revisar Colonia dentro del grupo de ciudad
            colonia_groups = ciudad_group.groupby('Colonia')
            
            for colonia_val, colonia_group in colonia_groups:
                if len(colonia_group) <= 1:
                    continue
                    
                # Revisar precio dentro del grupo de colonia
                precio_groups = colonia_group.groupby('precio')
                
                for precio_val, precio_group in precio_groups:
                    if len(precio_group) <= 1:
                        continue
                        
                    # Revisar longitud dentro del grupo de precio
                    lng_groups = precio_group.groupby('longitud')
                    
                    for lng_val, lng_group in lng_groups:
                        if len(lng_group) <= 1:
                            continue
                            
                        # Revisar latitud dentro del grupo de longitud
                        lat_groups = lng_group.groupby('latitud')
                        
                        for lat_val, lat_group in lat_groups:
                            if len(lat_group) <= 1:
                                continue
                                
                            # Revisar recamaras y baños como último nivel
                            banos_col = 'Banos_totales' if 'Banos_totales' in lat_group.columns else 'banos_icon'
                            final_groups = lat_group.groupby(['recamaras', banos_col])
                            
                            for final_vals, final_group in final_groups:
                                if len(final_group) > 1:
                                    # Marcar como duplicados todos excepto el primero
                                    dup_indices = final_group.index[1:]  # Mantener el primero, marcar el resto
                                    duplicates_mask.loc[dup_indices] = True
    
    # Separar únicos y duplicados
    unique_df = df[~duplicates_mask].copy()
    duplicate_df = df[duplicates_mask].copy()
    
    log.info(f"Detección de duplicados completada: {len(unique_df)} únicos, {len(duplicate_df)} duplicados")
    
    return unique_df, duplicate_df

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
    log.info(f'IDs únicos después de eliminar duplicados: {len(ids_final)}')
    
    # Verificar que los archivos de texto tengan los mismos IDs
    a_ids = set(a_df['id']) if 'id' in a_df.columns else set()
    b_ids = set(b_df['id']) if 'id' in b_df.columns else set()
    
    log.info(f'IDs en archivo MKT original: {len(a_ids)}')
    log.info(f'IDs en archivo AME original: {len(b_ids)}')
    
    # Filtrar usando solo los IDs que quedaron después de eliminar duplicados
    # CREAR DataFrames con TODOS los IDs de dedup_num, incluso si faltan en archivos de texto
    ids_final_df = dedup_num[['id']].copy()  # Base con todos los IDs finales
    
    # LEFT JOIN para asegurar que todos los IDs estén presentes
    a_final = ids_final_df.merge(a_df, on='id', how='left')
    b_final = ids_final_df.merge(b_df, on='id', how='left')
    
    log.info(f'IDs en archivo MKT después de merge: {len(a_final)}')
    log.info(f'IDs en archivo AME después de merge: {len(b_final)}')
    
    # Verificar si hay IDs duplicados en los archivos de texto después del merge
    a_duplicates = a_final['id'].duplicated().sum()
    b_duplicates = b_final['id'].duplicated().sum()
    
    if a_duplicates > 0:
        log.warning(f'Encontrados {a_duplicates} IDs duplicados en archivo MKT después de merge')
        a_final = a_final.drop_duplicates(subset=['id'], keep='first')
        log.info(f'IDs en archivo MKT después de eliminar duplicados: {len(a_final)}')
    
    if b_duplicates > 0:
        log.warning(f'Encontrados {b_duplicates} IDs duplicados en archivo AME después de merge')
        b_final = b_final.drop_duplicates(subset=['id'], keep='first')
        log.info(f'IDs en archivo AME después de eliminar duplicados: {len(b_final)}')
    
    # Verificación final: asegurar que todos los archivos tengan los mismos IDs
    final_num_ids = set(dedup_num['id'])
    final_a_ids = set(a_final['id'])
    final_b_ids = set(b_final['id'])
    
    # Ahora TODOS deberían tener exactamente los mismos IDs
    if len(final_num_ids) != len(final_a_ids) or len(final_num_ids) != len(final_b_ids):
        log.error(f'❌ INCONSISTENCIA DESPUÉS DE MERGE: NUM={len(final_num_ids)}, MKT={len(final_a_ids)}, AME={len(final_b_ids)}')
        
        # Identificar IDs faltantes o extra (esto NO debería pasar después del merge)
        missing_in_a = final_num_ids - final_a_ids
        missing_in_b = final_num_ids - final_b_ids
        extra_in_a = final_a_ids - final_num_ids
        extra_in_b = final_b_ids - final_num_ids
        
        if missing_in_a:
            log.error(f'❌ IDs faltantes en MKT: {len(missing_in_a)} IDs - ESTO NO DEBERÍA PASAR')
        if missing_in_b:
            log.error(f'❌ IDs faltantes en AME: {len(missing_in_b)} IDs - ESTO NO DEBERÍA PASAR')
        if extra_in_a:
            log.error(f'❌ IDs extra en MKT: {len(extra_in_a)} IDs - ESTO NO DEBERÍA PASAR')
        if extra_in_b:
            log.error(f'❌ IDs extra en AME: {len(extra_in_b)} IDs - ESTO NO DEBERÍA PASAR')
            
        # Última corrección de emergencia
        a_final = a_final[a_final['id'].isin(final_num_ids)].copy()
        b_final = b_final[b_final['id'].isin(final_num_ids)].copy()
        
        log.warning(f'⚠️ Corrección de emergencia aplicada: NUM={len(dedup_num)}, MKT={len(a_final)}, AME={len(b_final)}')
    else:
        log.info(f'✅ CONSISTENCIA PERFECTA: todos los archivos tienen exactamente {len(final_num_ids)} registros')
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
