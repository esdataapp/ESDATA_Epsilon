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
    "antiguedad_icon","PxM2","outlier_justificado_por_antiguedad"
]

# Constantes para superficie teórica (solo departamentos)
SUPERFICIE_TEORICA = {
    'recamara': 9.45,      # m²
    'bano_completo': 3.96,  # m²
    'medio_bano': 1.5,      # m²
    'cocina': 7.5,          # m²
    'sala_estancia': 15.75  # m²
}

# Condiciones específicas por tipo de propiedad y operación (ACTUALIZADAS SEGÚN DIRECTRICES)
PROPERTY_CONDITIONS = {
    # Departamentos en Venta (LÍMITES OPTIMIZADOS SEGÚN DIRECTRICES)
    ('departamento', 'venta'): {
        'area_min': 30, 'area_max': 200,
        'precio_min': 500000, 'precio_max': 25000000,
        'pxm2_min': 12500, 'pxm2_max': 150000,
        'recamaras_min': 1, 'recamaras_max': 3,
        'banos_min': 1, 'banos_max': 4.5
    },
    # Casas en Venta (LÍMITES OPTIMIZADOS SEGÚN DIRECTRICES)
    ('casa', 'venta'): {
        'area_min': 30, 'area_max': 1000,
        'precio_min': 500000, 'precio_max': 45000000,
        'pxm2_min': 5000, 'pxm2_max': 85555,
        'recamaras_min': 1, 'recamaras_max': 4,
        'banos_min': 1, 'banos_max': 5.5
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

def _imputation_and_correction(df: pd.DataFrame):
    """
    1. IMPUTACIÓN Y CORRECCIÓN INICIAL
    Intenta corregir valores nulos o atípicos antes de eliminar registros.
    Prioridad: Salvar la mayor cantidad de registros posibles.
    """
    corrected_records = 0
    imputed_records = 0
    corrections_log = []
    
    log.info("🔧 Iniciando imputación y corrección inicial...")
    
    df_corrected = df.copy()
    
    for idx, row in df.iterrows():
        changes = []
        original_recamaras = row.get('recamaras')
        original_banos = row.get('Banos_totales')
        original_estacionamientos = row.get('estacionamientos')
        area = row.get('area_m2')
        
        # IMPUTACIÓN DE RECÁMARAS basada en área
        if pd.isna(original_recamaras) or original_recamaras <= 0:
            if pd.notna(area) and area > 0:
                # Estimación: 1 recámara por cada 45 m², mínimo 1, máximo 4
                recamaras_estimadas = max(1, min(4, round(area / 45)))
                df_corrected.loc[df_corrected.index == idx, 'recamaras'] = recamaras_estimadas
                changes.append(f'recamaras_imputadas_{recamaras_estimadas}')
                imputed_records += 1
        
        # IMPUTACIÓN DE BAÑOS basada en recámaras
        recamaras_actual = df_corrected.loc[df_corrected.index == idx, 'recamaras'].iloc[0]
        if pd.isna(original_banos) or original_banos <= 0:
            if pd.notna(recamaras_actual) and recamaras_actual > 0:
                # Estimación: 1 baño por recámara como mínimo, máximo 1.5 * recámaras
                banos_estimados = min(recamaras_actual * 1.5, recamaras_actual + 1)
                df_corrected.loc[df_corrected.index == idx, 'Banos_totales'] = banos_estimados
                changes.append(f'banos_imputados_{banos_estimados}')
                imputed_records += 1
        
        # IMPUTACIÓN DE ESTACIONAMIENTOS basada en recámaras
        if pd.isna(original_estacionamientos) or original_estacionamientos < 0:
            if pd.notna(recamaras_actual) and recamaras_actual > 0:
                # Estimación: 1 estacionamiento por recámara, máximo recámaras + 1
                estacionamientos_estimados = min(recamaras_actual, recamaras_actual + 1)
                df_corrected.loc[df_corrected.index == idx, 'estacionamientos'] = estacionamientos_estimados
                changes.append(f'estacionamientos_imputados_{estacionamientos_estimados}')
                imputed_records += 1
        
        # CORRECCIÓN DE VALORES ATÍPICOS POR ERRORES DE DIGITACIÓN
        banos_actual = df_corrected.loc[df_corrected.index == idx, 'Banos_totales'].iloc[0]
        estacionamientos_actual = df_corrected.loc[df_corrected.index == idx, 'estacionamientos'].iloc[0]
        
        # Corrección de baños (posibles errores como 25 en lugar de 2.5)
        if pd.notna(banos_actual) and banos_actual >= 10:
            if banos_actual % 10 == 5:  # Caso: 25 -> 2.5
                nuevo_banos = banos_actual / 10
                df_corrected.loc[df_corrected.index == idx, 'Banos_totales'] = nuevo_banos
                changes.append(f'banos_corregidos_{banos_actual}_a_{nuevo_banos}')
                corrected_records += 1
            elif banos_actual % 10 == 0:  # Caso: 20 -> 2.0
                nuevo_banos = banos_actual / 10
                df_corrected.loc[df_corrected.index == idx, 'Banos_totales'] = nuevo_banos
                changes.append(f'banos_corregidos_{banos_actual}_a_{nuevo_banos}')
                corrected_records += 1
        
        # Corrección de estacionamientos (posibles errores como 30 en lugar de 3)
        if pd.notna(estacionamientos_actual) and estacionamientos_actual >= 10:
            nuevo_estacionamientos = estacionamientos_actual / 10
            if nuevo_estacionamientos <= 6:  # Máximo razonable
                df_corrected.loc[df_corrected.index == idx, 'estacionamientos'] = nuevo_estacionamientos
                changes.append(f'estacionamientos_corregidos_{estacionamientos_actual}_a_{nuevo_estacionamientos}')
                corrected_records += 1
        
        if changes:
            corrections_log.append(f"ID {row.get('id', 'unknown')}: {', '.join(changes)}")
    
    log.info(f"✅ Imputación completada:")
    log.info(f"   � Registros con imputaciones: {imputed_records}")
    log.info(f"   🔧 Registros con correcciones: {corrected_records}")
    
    if corrections_log and len(corrections_log) <= 20:
        log.info("📝 Ejemplos de correcciones aplicadas:")
        for example in corrections_log[:10]:
            log.info(f"   • {example}")
    
    return df_corrected

def _validate_room_coherence(df: pd.DataFrame):
    """
    2. VALIDACIÓN DE COHERENCIA ENTRE HABITACIONES
    Aplica las reglas para detectar outliers lógicos que deben ser eliminados.
    """
    log.info("🏠 Validando coherencia entre habitaciones...")
    
    violations = []
    for idx, row in df.iterrows():
        row_violations = []
        
        recamaras = row.get('recamaras')
        banos = row.get('Banos_totales')
        estacionamientos = row.get('estacionamientos')
        
        # Regla de Baños: baños <= recámaras + 1.5
        if pd.notna(recamaras) and pd.notna(banos) and recamaras > 0:
            if banos > (recamaras + 1.5):
                row_violations.append(f'banos_excesivos_{banos}_vs_rec_{recamaras}')
        
        # Regla de Estacionamientos: estacionamientos <= recámaras + 1
        if pd.notna(recamaras) and pd.notna(estacionamientos) and recamaras > 0:
            if estacionamientos > (recamaras + 1):
                row_violations.append(f'estacionamientos_excesivos_{estacionamientos}_vs_rec_{recamaras}')
        
        if row_violations:
            violations.append((idx, ';'.join(row_violations)))
    
    violation_indices = [v[0] for v in violations]
    valid_df = df.drop(index=violation_indices)
    invalid_df = df.loc[violation_indices].copy()
    
    if violations:
        invalid_df['motivos_eliminacion'] = [v[1] for v in violations]
    
    log.info(f"   ✅ Registros válidos: {len(valid_df):,}")
    log.info(f"   ❌ Registros eliminados por coherencia: {len(invalid_df):,}")
    
    return valid_df, invalid_df


def _verify_surface_logic_departments(df: pd.DataFrame):
    """
    3. VERIFICACIÓN DE SUPERFICIE LÓGICA (Solo para Departamentos)
    Implementa sanity check para validar coherencia entre superficie reportada y calculada.
    """
    log.info("📐 Verificando lógica de superficie para departamentos...")
    
    # Filtrar solo departamentos
    departamentos = df[df['tipo_propiedad'].str.lower().str.contains('dep', na=False)].copy()
    otros = df[~df['tipo_propiedad'].str.lower().str.contains('dep', na=False)].copy()
    
    if len(departamentos) == 0:
        log.info("   ⚠️ No hay departamentos para verificar superficie")
        return df, pd.DataFrame()
    
    violations = []
    
    for idx, row in departamentos.iterrows():
        recamaras = row.get('recamaras', 0)
        banos_totales = row.get('Banos_totales', 0)
        area_reportada = row.get('area_m2', 0)
        
        if pd.notna(recamaras) and pd.notna(banos_totales) and pd.notna(area_reportada):
            if recamaras > 0 and banos_totales > 0 and area_reportada > 0:
                # Calcular superficie teórica
                banos_completos = int(banos_totales)
                medios_banos = 1 if (banos_totales % 1) >= 0.5 else 0
                
                superficie_teorica = (
                    recamaras * SUPERFICIE_TEORICA['recamara'] +
                    banos_completos * SUPERFICIE_TEORICA['bano_completo'] +
                    medios_banos * SUPERFICIE_TEORICA['medio_bano'] +
                    SUPERFICIE_TEORICA['cocina'] +
                    SUPERFICIE_TEORICA['sala_estancia']
                )
                
                # Validación: discrepancia extrema (factor de 5)
                ratio = area_reportada / superficie_teorica if superficie_teorica > 0 else 0
                
                if ratio < 0.2 or ratio > 5.0:  # Discrepancia extrema
                    violations.append((idx, f'superficie_incoherente_rep_{area_reportada}_teo_{superficie_teorica:.1f}_ratio_{ratio:.2f}'))
    
    violation_indices = [v[0] for v in violations]
    valid_departamentos = departamentos.drop(index=violation_indices)
    invalid_departamentos = departamentos.loc[violation_indices].copy()
    
    if violations:
        invalid_departamentos['motivos_eliminacion'] = [v[1] for v in violations]
    
    # Combinar departamentos válidos con otros tipos de propiedad
    valid_df = pd.concat([valid_departamentos, otros], ignore_index=True)
    
    log.info(f"   📊 Departamentos analizados: {len(departamentos):,}")
    log.info(f"   ✅ Departamentos con superficie coherente: {len(valid_departamentos):,}")
    log.info(f"   ❌ Departamentos eliminados por superficie: {len(invalid_departamentos):,}")
    
    return valid_df, invalid_departamentos


def _apply_optimal_property_filters(df: pd.DataFrame):
    """
    4. FILTRO FINAL POR RANGOS DE PROPIEDAD ÓPTIMA
    Aplica filtros específicos según las directrices para departamentos y casas.
    """
    log.info("🎯 Aplicando filtros de propiedad óptima...")
    
    violations = []
    
    for idx, row in df.iterrows():
        row_violations = []
        
        tipo_propiedad = _normalize_property_type(row.get('tipo_propiedad'))
        operacion = _normalize_operation(row.get('operacion'))
        
        area = row.get('area_m2')
        precio = row.get('precio')
        pxm2 = row.get('PxM2')
        recamaras = row.get('recamaras')
        banos = row.get('Banos_totales')
        
        # Aplicar filtros específicos para departamentos y casas
        if tipo_propiedad in ['departamento', 'casa']:
            key = (tipo_propiedad, operacion)
            conditions = PROPERTY_CONDITIONS.get(key, {})
            
            if conditions:
                # Validar superficie
                if pd.notna(area) and ('area_min' in conditions and 'area_max' in conditions):
                    if area < conditions['area_min'] or area > conditions['area_max']:
                        row_violations.append(f'superficie_fuera_rango_{area}_{conditions["area_min"]}-{conditions["area_max"]}')
                
                # Validar precio
                if pd.notna(precio) and ('precio_min' in conditions and 'precio_max' in conditions):
                    if precio < conditions['precio_min'] or precio > conditions['precio_max']:
                        row_violations.append(f'precio_fuera_rango_{precio}_{conditions["precio_min"]}-{conditions["precio_max"]}')
                
                # Validar PxM2
                if pd.notna(pxm2) and ('pxm2_min' in conditions and 'pxm2_max' in conditions):
                    if pxm2 < conditions['pxm2_min'] or pxm2 > conditions['pxm2_max']:
                        row_violations.append(f'pxm2_fuera_rango_{pxm2}_{conditions["pxm2_min"]}-{conditions["pxm2_max"]}')
                
                # Validar recámaras
                if pd.notna(recamaras) and ('recamaras_min' in conditions and 'recamaras_max' in conditions):
                    if recamaras < conditions['recamaras_min'] or recamaras > conditions['recamaras_max']:
                        row_violations.append(f'recamaras_fuera_rango_{recamaras}_{conditions["recamaras_min"]}-{conditions["recamaras_max"]}')
                
                # Validar baños
                if pd.notna(banos) and ('banos_min' in conditions and 'banos_max' in conditions):
                    if banos < conditions['banos_min'] or banos > conditions['banos_max']:
                        row_violations.append(f'banos_fuera_rango_{banos}_{conditions["banos_min"]}-{conditions["banos_max"]}')
        
        if row_violations:
            violations.append((idx, ';'.join(row_violations)))
    
    violation_indices = [v[0] for v in violations]
    valid_df = df.drop(index=violation_indices)
    invalid_df = df.loc[violation_indices].copy()
    
    if violations:
        invalid_df['motivos_eliminacion'] = [v[1] for v in violations]
    
    log.info(f"   ✅ Propiedades óptimas: {len(valid_df):,}")
    log.info(f"   ❌ Propiedades eliminadas por filtros: {len(invalid_df):,}")
    
    return valid_df, invalid_df

def _repair_antiguedad(df: pd.DataFrame):
    """Repara valores de antigüedad_icon que sean demasiado altos"""
    corrected_antiguedad = 0
    df_corrected = df.copy()
    
    for idx, row in df.iterrows():
        antiguedad = row.get('antiguedad_icon')
        
        if pd.notna(antiguedad) and isinstance(antiguedad, (int, float)):
            # Si la antigüedad es mayor a 100, probablemente le faltan ceros
            if antiguedad > 100:
                # Intentar convertir a años (asumir que es año de construcción)
                from datetime import datetime
                current_year = datetime.now().year
                
                if antiguedad > 1900 and antiguedad <= current_year:
                    # Es un año de construcción, convertir a antigüedad
                    nueva_antiguedad = current_year - antiguedad
                    df_corrected.loc[df_corrected.index == idx, 'antiguedad_icon'] = nueva_antiguedad
                    corrected_antiguedad += 1
                elif antiguedad >= 1000:
                    # Probablemente le sobran dígitos, dividir entre 10
                    nueva_antiguedad = antiguedad / 10
                    if nueva_antiguedad <= 100:
                        df_corrected.loc[df_corrected.index == idx, 'antiguedad_icon'] = nueva_antiguedad
                        corrected_antiguedad += 1
            
            # Si la antigüedad es mayor a 100 años (muy improbable), marcar como outlier
            elif antiguedad > 100:
                df_corrected.loc[df_corrected.index == idx, 'antiguedad_icon'] = np.nan  # Se eliminará en el filtrado
    
    if corrected_antiguedad > 0:
        print(f"🔧 Corregidas {corrected_antiguedad} antigüedades inconsistentes")
    
    return df_corrected

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
    """Filtrar propiedades usando condiciones específicas por tipo y operación + reglas lógicas"""
    print(f"🔍 Iniciando filtrado de {len(df)} propiedades")
    
    motivos = []
    keep_idx = []
    drop_rows = []
    
    # Contadores para debug
    tipo_counts = {}
    conditions_used = {}
    logical_violations = {'banos': 0, 'estacionamientos': 0, 'coherencia': 0, 'antiguedad': 0}
    
    for idx, row in df.iterrows():
        row_motivos = []
        precio = row.get('precio')
        area = row.get('area_m2')
        tipo = row.get('tipo_propiedad')
        operacion = row.get('operacion')
        pxm2 = row.get('PxM2')
        recamaras = row.get('recamaras')
        banos = row.get('Banos_totales')
        estacionamientos = row.get('estacionamientos')
        antiguedad = row.get('antiguedad_icon')
        coherencia = row.get('coherencia_fisica')

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
        
        # NUEVAS REGLAS LÓGICAS
        
        # 1. Regla de Baños: baños <= recámaras + 1.5
        if pd.notna(recamaras) and pd.notna(banos) and recamaras > 0:
            max_banos_logico = recamaras + 1.5
            if banos > max_banos_logico:
                row_motivos.append(f'banos_logica_violada_{banos}_vs_{max_banos_logico}')
                logical_violations['banos'] += 1
        
        # 2. Regla de Estacionamientos: estacionamientos <= recámaras + 1
        if pd.notna(recamaras) and pd.notna(estacionamientos) and recamaras > 0:
            max_estacionamientos_logico = recamaras + 1
            if estacionamientos > max_estacionamientos_logico:
                row_motivos.append(f'estacionamientos_logica_violada_{estacionamientos}_vs_{max_estacionamientos_logico}')
                logical_violations['estacionamientos'] += 1
        
        # 3. Coherencia Física (solo para departamentos con coherencia calculada)
        if pd.notna(coherencia):
            # Coherencia muy baja (área real << área esperada) o muy alta (área real >> área esperada)
            if coherencia < 0.3 or coherencia > 3.0:
                row_motivos.append(f'coherencia_fisica_invalida_{coherencia:.2f}')
                logical_violations['coherencia'] += 1
        
        # 4. Antigüedad lógica (no mayor a 100 años)
        if pd.notna(antiguedad) and isinstance(antiguedad, (int, float)):
            if antiguedad > 100:
                row_motivos.append(f'antiguedad_logica_violada_{antiguedad}')
                logical_violations['antiguedad'] += 1
        
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
            
            # Filtros adicionales para recámaras y baños (si existen en las condiciones)
            if 'recamaras_min' in conditions and 'recamaras_max' in conditions:
                if pd.notna(recamaras) and (recamaras < conditions['recamaras_min'] or recamaras > conditions['recamaras_max']):
                    row_motivos.append(f'recamaras_fuera_rango_{conditions["recamaras_min"]}-{conditions["recamaras_max"]}')
            
            if 'banos_min' in conditions and 'banos_max' in conditions:
                if pd.notna(banos) and (banos < conditions['banos_min'] or banos > conditions['banos_max']):
                    row_motivos.append(f'banos_fuera_rango_{conditions["banos_min"]}-{conditions["banos_max"]}')

        if row_motivos:
            drop_rows.append(idx)
            motivos.append((idx, ';'.join(row_motivos)))
        else:
            keep_idx.append(idx)

    # Debug info
    print(f"📊 Tipos encontrados: {tipo_counts}")
    print(f"🎯 Condiciones utilizadas: {conditions_used}")
    print(f"⚖️ Violaciones lógicas: {logical_violations}")
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
    
    log.info('🔧 Aplicando validación comprehensiva...')
    improved, eliminated_records = _apply_comprehensive_validation(improved)
    
    log.info('⏳ Reparando valores de antigüedad...')
    improved = _repair_antiguedad(improved)
    
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

def _correct_age_anomalies(df: pd.DataFrame):
    """
    5. CORRECCIÓN DE ANTIGÜEDAD ANÓMALA (NO ELIMINATORIA)
    Corrige valores obvios de error de captura pero mantiene todas las propiedades.
    """
    log.info("📅 Corrigiendo anomalías obvias de antigüedad...")
    
    if 'antiguedad_icon' not in df.columns:
        log.warning("   ⚠️ Columna 'antiguedad_icon' no encontrada")
        return df
    
    corrections_made = 0
    
    # Usar máscaras para corregir errores obvios de captura
    mask_year_error = df['antiguedad_icon'] > 200
    if mask_year_error.sum() > 0:
        df.loc[mask_year_error, 'antiguedad_icon'] = 2025 - df.loc[mask_year_error, 'antiguedad_icon']
        corrections_made += mask_year_error.sum()
    
    # Posible confusión meses/años (110-200 años)
    mask_months = (df['antiguedad_icon'] > 110) & (df['antiguedad_icon'] <= 200)
    if mask_months.sum() > 0:
        df.loc[mask_months, 'antiguedad_icon'] = df.loc[mask_months, 'antiguedad_icon'] / 12
        corrections_made += mask_months.sum()
    
    # Posible error de entrada (25-110 años)
    mask_decimal = (df['antiguedad_icon'] > 25) & (df['antiguedad_icon'] <= 110)
    if mask_decimal.sum() > 0:
        df.loc[mask_decimal, 'antiguedad_icon'] = df.loc[mask_decimal, 'antiguedad_icon'] / 10
        corrections_made += mask_decimal.sum()
    
    if corrections_made > 0:
        log.info(f"   🔧 Correcciones aplicadas: {corrections_made:,} registros")
    else:
        log.info("   ✅ No se encontraron anomalías obvias de antigüedad")
    
    return df


def _analyze_age_context_for_outliers(df: pd.DataFrame):
    """
    6. ANÁLISIS CONTEXTUAL DE ANTIGÜEDAD PARA OUTLIERS
    Usa la antigüedad como factor contextual para entender outliers de precio/superficie.
    NO elimina propiedades, solo marca outliers justificados por antigüedad.
    """
    log.info("🏛️ Analizando contexto de antigüedad para outliers...")
    
    if 'antiguedad_icon' not in df.columns:
        log.warning("   ⚠️ Columna 'antiguedad_icon' no encontrada")
        df['outlier_justificado_por_antiguedad'] = False
        return df
    
    # Inicializar columna
    df['outlier_justificado_por_antiguedad'] = False
    
    # Identificar outliers justificados por antigüedad
    mask_muy_antigua = df['antiguedad_icon'] > 50
    mask_precio_bajo = df['PxM2'] < 8000
    mask_superficie_atipica = (df['area_m2'] > 500) | (df['area_m2'] < 25)
    
    # Propiedades muy antiguas con precio bajo
    mask_justificado_1 = mask_muy_antigua & mask_precio_bajo
    
    # Propiedades muy antiguas con superficie atípica
    mask_justificado_2 = mask_muy_antigua & mask_superficie_atipica
    
    # Propiedades antiguas (20-50 años) con descuento moderado
    mask_antigua = (df['antiguedad_icon'] > 20) & (df['antiguedad_icon'] <= 50)
    mask_descuento = df['PxM2'] < 10000
    mask_justificado_3 = mask_antigua & mask_descuento
    
    # Aplicar todas las justificaciones
    mask_total_justificado = mask_justificado_1 | mask_justificado_2 | mask_justificado_3
    df.loc[mask_total_justificado, 'outlier_justificado_por_antiguedad'] = True
    
    justificados = mask_total_justificado.sum()
    
    log.info(f"   ✅ Outliers justificados por antigüedad: {justificados:,}")
    log.info(f"   📊 Propiedades analizadas con antigüedad: {df['antiguedad_icon'].notna().sum():,}")
    
    return df


def _apply_comprehensive_validation(df: pd.DataFrame):
    """
    PIPELINE COMPLETO DE VALIDACIÓN
    Implementa las 6 directrices de mejora en orden secuencial.
    """
    log.info("🔍 Iniciando validación comprehensiva...")
    
    initial_count = len(df)
    all_eliminated = []
    
    # 1. Imputación y corrección inicial
    df = _imputation_and_correction(df)
    log.info(f"   Después de imputación: {len(df):,} registros")
    
    # 2. Validación de coherencia entre habitaciones
    df, eliminated_coherence = _validate_room_coherence(df)
    if len(eliminated_coherence) > 0:
        all_eliminated.append(eliminated_coherence)
    
    # 3. Verificación de superficie lógica (departamentos)
    df, eliminated_surface = _verify_surface_logic_departments(df)
    if len(eliminated_surface) > 0:
        all_eliminated.append(eliminated_surface)
    
    # 4. Filtros de propiedad óptima
    df, eliminated_filters = _apply_optimal_property_filters(df)
    if len(eliminated_filters) > 0:
        all_eliminated.append(eliminated_filters)
    
    # 5. Corrección de antigüedad anómala (no eliminatoria)
    df = _correct_age_anomalies(df)
    
    # 6. Análisis contextual de antigüedad para outliers (no eliminatoria)
    df = _analyze_age_context_for_outliers(df)
    
    # Consolidar todos los eliminados (sin incluir antigüedad)
    final_eliminated = pd.concat(all_eliminated, ignore_index=True) if all_eliminated else pd.DataFrame()
    
    final_count = len(df)
    eliminated_count = initial_count - final_count
    
    log.info(f"🎯 RESUMEN VALIDACIÓN COMPREHENSIVA:")
    log.info(f"   📊 Registros iniciales: {initial_count:,}")
    log.info(f"   ✅ Registros válidos finales: {final_count:,}")
    log.info(f"   ❌ Registros eliminados total: {eliminated_count:,}")
    log.info(f"   📈 Tasa de retención: {(final_count/initial_count)*100:.1f}%")
    
    return df, final_eliminated


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
