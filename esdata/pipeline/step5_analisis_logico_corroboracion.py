"""Paso 5: Análisis Lógico y Corroboración con Condiciones Específicas

Combina 3a (num) + 4a (texto) para validar y corregir usando condiciones específicas por tipo de propiedad.

Condiciones implementadas:
- Departamentos en Venta: área 30-355 m², precio $500K-25M, PxM2 $12.5K-150K
- Casas en Venta: área 30-1000 m², precio $500K-45M, PxM2 $5K-85.6K  
- Local Comercial en Venta: área 30-1255 m², precio $250K-35M, PxM2 $5K-100K
- Oficinas en Venta: área 30-1555 m², precio $250K-60M, PxM2 $5K-110K
- Terreno en Venta: área 30-2055 m², precio $150K-45M, PxM2 $350-50K
- Departamentos en Renta: área 30-355 m², precio $5K-135K, PxM2 $70-580

Salidas:
    - 5.Num_Corroborado_<Periodo>.csv (registros válidos)
    - Datos_Filtrados/Eliminados/<Periodo>/paso5_invalidos_<Periodo>.csv (registros con motivos)
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

# Condiciones específicas por tipo de propiedad y operación
PROPERTY_CONDITIONS = {
    # Departamentos en Venta
    ('departamento', 'venta'): {
        'area_min': 30, 'area_max': 355,
        'precio_min': 500000, 'precio_max': 25000000,
        'pxm2_min': 12500, 'pxm2_max': 150000
    },
    # Casas en Venta
    ('casa', 'venta'): {
        'area_min': 30, 'area_max': 1000,
        'precio_min': 500000, 'precio_max': 45000000,
        'pxm2_min': 5000, 'pxm2_max': 85555
    },
    # Local Comercial en Venta
    ('local', 'venta'): {
        'area_min': 30, 'area_max': 1255,
        'precio_min': 250000, 'precio_max': 35000000,
        'pxm2_min': 5000, 'pxm2_max': 100000
    },
    # Oficinas en Venta
    ('oficina', 'venta'): {
        'area_min': 30, 'area_max': 1555,
        'precio_min': 250000, 'precio_max': 60000000,
        'pxm2_min': 5000, 'pxm2_max': 110000
    },
    # Terreno en Venta
    ('terreno', 'venta'): {
        'area_min': 30, 'area_max': 2055,
        'precio_min': 150000, 'precio_max': 45000000,
        'pxm2_min': 350, 'pxm2_max': 50000
    },
    # Departamentos en Renta
    ('departamento', 'renta'): {
        'area_min': 30, 'area_max': 355,
        'precio_min': 5000, 'precio_max': 135000,
        'pxm2_min': 70, 'pxm2_max': 580
    },
    # Casas en Renta (condiciones estimadas basadas en proporciones de venta)
    ('casa', 'renta'): {
        'area_min': 30, 'area_max': 1000,
        'precio_min': 8000, 'precio_max': 180000,
        'pxm2_min': 100, 'pxm2_max': 600
    },
    # Local Comercial en Renta (condiciones estimadas)
    ('local', 'renta'): {
        'area_min': 30, 'area_max': 1255,
        'precio_min': 5000, 'precio_max': 150000,
        'pxm2_min': 80, 'pxm2_max': 500
    },
    # Oficinas en Renta (condiciones estimadas)
    ('oficina', 'renta'): {
        'area_min': 30, 'area_max': 1555,
        'precio_min': 6000, 'precio_max': 200000,
        'pxm2_min': 100, 'pxm2_max': 550
    },
    # Terreno en Renta (condiciones estimadas - casos raros)
    ('terreno', 'renta'): {
        'area_min': 100, 'area_max': 2055,
        'precio_min': 2000, 'precio_max': 50000,
        'pxm2_min': 5, 'pxm2_max': 150
    }
}


def _normalize_property_type(tipo):
    """Normaliza el tipo de propiedad a los valores estándar"""
    if pd.isna(tipo):
        return 'unknown'
    
    tipo_str = str(tipo).strip()
    tipo_lower = tipo_str.lower()
    
    # Primero verificar si es un código estandarizado
    if tipo_str in ['Dep', 'Departamentos']:
        return 'departamento'
    elif tipo_str in ['Cas', 'Casa']:
        return 'casa'
    elif tipo_str in ['LocC', 'Local Comercial', 'Loc']:
        return 'local'
    elif tipo_str in ['Ofc', 'Oficina']:
        return 'oficina'
    elif tipo_str in ['Terr', 'Terreno', 'Lote']:
        return 'terreno'
    
    # Luego verificar texto completo en minúsculas
    if any(word in tipo_lower for word in ['dep', 'depart', 'apartment']):
        return 'departamento'
    elif any(word in tipo_lower for word in ['cas', 'house', 'vivienda']):
        return 'casa'
    elif any(word in tipo_lower for word in ['local', 'comercial', 'negocio']):
        return 'local'
    elif any(word in tipo_lower for word in ['oficina', 'office']):
        return 'oficina'
    elif any(word in tipo_lower for word in ['terreno', 'lote', 'land']):
        return 'terreno'
    else:
        return tipo_lower

def _normalize_operation(operacion):
    """Normaliza la operación a los valores estándar"""
    if pd.isna(operacion):
        return 'unknown'
    
    op_str = str(operacion).strip()
    op_lower = op_str.lower()
    
    # Primero verificar valores directos y códigos estandarizados
    if op_str in ['Venta', 'venta', 'Ven', 'ven']:
        return 'venta'
    elif op_str in ['Renta', 'renta', 'Ren', 'ren']:
        return 'renta'
    
    # Luego verificar patrones en minúsculas
    if any(word in op_lower for word in ['vent', 'sell', 'sale']):
        return 'venta'
    elif any(word in op_lower for word in ['rent', 'alquil', 'arrend']):
        return 'renta'
    else:
        return op_lower

def _merge(num_df, tex_df):
    """Combina los DataFrames numérico y de texto"""
    return pd.merge(num_df, tex_df, on='id', how='left', suffixes=('', '_texto'))

def _improve(df):
    """Mejora los datos reemplazando valores faltantes desde texto"""
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

def _get_property_conditions(tipo_propiedad, operacion):
    """Obtener condiciones para un tipo de propiedad y operación específicos"""
    tipo_norm = _normalize_property_type(tipo_propiedad)
    op_norm = _normalize_operation(operacion)
    
    key = (tipo_norm, op_norm)
    if key in PROPERTY_CONDITIONS:
        return PROPERTY_CONDITIONS[key]
    else:
        # Si no hay condiciones específicas, usar valores por defecto MÁS ESTRICTOS
        # (Se reportará en el resumen final, no por cada caso individual)
        return {
            'area_min': 30, 'area_max': 500,
            'precio_min': 100000, 'precio_max': 20000000,
            'pxm2_min': 1000, 'pxm2_max': 80000
        }

def _logic_filter(df: pd.DataFrame):
    """Filtrar propiedades usando condiciones específicas por tipo y operación"""
    print(f"🔍 Iniciando filtrado de {len(df)} propiedades")
    
    motivos = []
    keep_idx = []
    drop_rows = []
    
    # Contadores para debug
    tipo_counts = {}
    conditions_used = {}
    
    for idx, row in df.iterrows():
        row_motivos = []
        precio = row.get('precio')
        area = row.get('area_m2')
        tipo = row.get('tipo_propiedad')
        operacion = row.get('operacion')
        pxm2 = row.get('PxM2')

        # Debug: contar tipos
        tipo_norm = _normalize_property_type(tipo)
        op_norm = _normalize_operation(operacion)
        key = (tipo_norm, op_norm)
        
        if tipo_norm not in tipo_counts:
            tipo_counts[tipo_norm] = 0
        tipo_counts[tipo_norm] += 1
        
        # Validaciones básicas
        if pd.isna(precio) or precio <= 0:
            row_motivos.append('precio_invalido')
        if pd.isna(area) or area <= 0:
            row_motivos.append('area_invalida')
        if pd.isna(pxm2) or pxm2 <= 0:
            row_motivos.append('pxm2_invalido')
        
        # Si faltan datos básicos, no podemos aplicar filtros específicos
        if not row_motivos:
            # Obtener condiciones específicas para esta propiedad
            conditions = _get_property_conditions(tipo, operacion)
            
            if key not in conditions_used:
                conditions_used[key] = 0
            conditions_used[key] += 1
            
            # Aplicar filtros específicos (con verificación adicional de nulos)
            if pd.notna(area) and (area < conditions['area_min'] or area > conditions['area_max']):
                row_motivos.append(f'area_fuera_rango_{conditions["area_min"]}-{conditions["area_max"]}')
            
            if pd.notna(precio) and (precio < conditions['precio_min'] or precio > conditions['precio_max']):
                row_motivos.append(f'precio_fuera_rango_{conditions["precio_min"]}-{conditions["precio_max"]}')
            
            if pd.notna(pxm2) and (pxm2 < conditions['pxm2_min'] or pxm2 > conditions['pxm2_max']):
                row_motivos.append(f'pxm2_fuera_rango_{conditions["pxm2_min"]}-{conditions["pxm2_max"]}')

        if row_motivos:
            drop_rows.append(idx)
            motivos.append((idx, ';'.join(row_motivos)))
        else:
            keep_idx.append(idx)

    # Debug info
    print(f"📊 Tipos encontrados: {tipo_counts}")
    print(f"🎯 Condiciones utilizadas: {conditions_used}")
    print(f"✅ Propiedades válidas: {len(keep_idx)}")
    print(f"❌ Propiedades eliminadas: {len(drop_rows)}")
    
    valid = df.loc[keep_idx].copy() if keep_idx else pd.DataFrame()
    invalid = df.loc[drop_rows].copy() if drop_rows else pd.DataFrame()
    
    if len(motivos) > 0:
        invalid['motivos_eliminacion'] = [m[1] for m in motivos]
    
    return valid, invalid

def run(periodo):
    log.info('=' * 80)
    log.info('🔍 INICIANDO STEP 5: ANÁLISIS LÓGICO Y CORROBORACIÓN')
    log.info('=' * 80)
    log.info(f'📅 Periodo: {periodo}')
    
    base_dir = os.path.join(path_consolidados(), periodo)
    num_path = os.path.join(base_dir, f'3a.Consolidado_Num_{periodo}.csv')
    tex_num_path = os.path.join(base_dir, f'4a.Tex_Titulo_Descripcion_{periodo}.csv')
    
    if not os.path.exists(num_path) or not os.path.exists(tex_num_path):
        raise FileNotFoundError('Faltan entradas para paso 5')
    
    log.info('📁 Cargando archivos de entrada...')
    log.info(f'   • Datos numéricos: {num_path}')
    log.info(f'   • Datos de texto: {tex_num_path}')
    
    num_df = read_csv(num_path)
    tex_df = read_csv(tex_num_path)
    
    log.info(f'✅ Datos cargados:')
    log.info(f'   • Registros numéricos: {len(num_df):,}')
    log.info(f'   • Registros de texto: {len(tex_df):,}')
    
    log.info('🔗 Combinando datos numéricos y de texto...')
    merged = _merge(num_df, tex_df)
    log.info(f'✅ Registros después de merge: {len(merged):,}')
    
    log.info('📈 Mejorando datos faltantes desde texto...')
    improved = _improve(merged)
    
    log.info('🧮 Calculando precio por metro cuadrado...')
    improved = _compute_pxm2(improved)
    
    # Estadísticas antes del filtrado
    precio_validos = improved['precio'].notna().sum()
    area_validos = improved['area_m2'].notna().sum()
    pxm2_validos = improved['PxM2'].notna().sum()
    
    log.info('📊 ESTADÍSTICAS PRE-FILTRADO:')
    log.info(f'   • Total propiedades: {len(improved):,}')
    log.info(f'   • Con precio válido: {precio_validos:,}')
    log.info(f'   • Con área válida: {area_validos:,}')
    log.info(f'   • Con PxM2 calculado: {pxm2_validos:,}')
    
    if not improved.empty:
        log.info('🏠 DISTRIBUCIÓN POR TIPO Y OPERACIÓN:')
        combinaciones = improved.groupby(['tipo_propiedad', 'operacion']).size().reset_index(name='count')
        for _, combo in combinaciones.iterrows():
            log.info(f'   • {combo["tipo_propiedad"]}-{combo["operacion"]}: {combo["count"]:,} propiedades')
    
    # Aplicar filtros específicos por tipo de propiedad
    log.info('🔍 Aplicando filtros lógicos por tipo de propiedad...')
    valid, invalid = _logic_filter(improved)
    
    # Estadísticas de filtrado
    total_eliminadas = len(invalid)
    tasa_retencion = (len(valid) / len(improved) * 100) if len(improved) > 0 else 0
    
    log.info('📊 RESULTADOS DEL FILTRADO:')
    log.info(f'   • Propiedades válidas: {len(valid):,}')
    log.info(f'   • Propiedades eliminadas: {total_eliminadas:,}')
    log.info(f'   • Tasa de retención: {tasa_retencion:.1f}%')
    
    # Análisis de motivos de eliminación
    if total_eliminadas > 0:
        log.info('⚠️ MOTIVOS DE ELIMINACIÓN:')
        motivos_count = {}
        for motivo_str in invalid['motivos_eliminacion']:
            for motivo in str(motivo_str).split(';'):
                motivos_count[motivo] = motivos_count.get(motivo, 0) + 1
        
        for motivo, count in sorted(motivos_count.items(), key=lambda x: x[1], reverse=True):
            log.info(f'   • {motivo}: {count:,} propiedades')
    
    out_valid = valid[[c for c in NUM_KEEP_COLS if c in valid.columns]].copy()
    output_path = os.path.join(base_dir, f'5.Num_Corroborado_{periodo}.csv')
    write_csv(out_valid, output_path)
    
    log.info('💾 ARCHIVO VÁLIDO GENERADO:')
    log.info(f'   • Ruta: {output_path}')
    log.info(f'   • Propiedades: {len(out_valid):,}')
    log.info(f'   • Columnas: {len(out_valid.columns)}')
    log.info(f'   • Tamaño: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB')
    
    if len(invalid) > 0:
        elim_dir = ensure_dir(path_base('Datos_Filtrados','Eliminados', periodo))
        invalid_path = os.path.join(elim_dir, f'paso5_invalidos_{periodo}.csv')
        write_csv(invalid, invalid_path)
        log.info('💾 ARCHIVO DE PROPIEDADES INVÁLIDAS:')
        log.info(f'   • Ruta: {invalid_path}')
        log.info(f'   • Propiedades eliminadas: {len(invalid):,}')
        log.info(f'   • Tamaño: {os.path.getsize(invalid_path) / 1024 / 1024:.2f} MB')
    
    # Resumen final por ciudad
    if not out_valid.empty:
        log.info('🏙️ DISTRIBUCIÓN FINAL POR CIUDAD:')
        for ciudad, count in out_valid['Ciudad'].value_counts().head(10).items():
            log.info(f'   • {ciudad}: {count:,} propiedades válidas')
    
    log.info('✅ STEP 5 COMPLETADO EXITOSAMENTE')
    log.info('=' * 80)
    
    return output_path

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Paso 5 Analisis Logico con Condiciones Específicas por Tipo de Propiedad')
    parser.add_argument('--periodo', help='Periodo (ej Sep25)', default=None)
    args = parser.parse_args()
    
    if args.periodo:
        per = args.periodo
    else:
        from datetime import datetime
        per = datetime.now().strftime('%b%y')
    
    run(per)
