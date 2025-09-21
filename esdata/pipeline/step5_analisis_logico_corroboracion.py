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

# Condiciones específicas por tipo de propiedad y operación (ACTUALIZADAS)
PROPERTY_CONDITIONS = {
    # Departamentos en Venta (LÍMITES OPTIMIZADOS)
    ('departamento', 'venta'): {
        'area_min': 30, 'area_max': 200,
        'precio_min': 500000, 'precio_max': 25000000,
        'pxm2_min': 12500, 'pxm2_max': 150000,
        'recamaras_min': 1, 'recamaras_max': 3,
        'banos_min': 1, 'banos_max': 4.5
    },
    # Casas en Venta (LÍMITES OPTIMIZADOS)
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

def _apply_logical_rules(df: pd.DataFrame):
    """Aplica reglas lógicas para corregir variables y detectar outliers"""
    corrected_rows = 0
    corrections_log = []
    
    # Crear copias para las modificaciones
    df_corrected = df.copy()
    
    for idx, row in df.iterrows():
        changes = []
        
        # 1. Regla de Baños: baños <= recámaras + 1.5
        recamaras = row.get('recamaras')
        banos = row.get('Banos_totales')
        
        if pd.notna(recamaras) and pd.notna(banos) and recamaras > 0:
            max_banos_logico = recamaras + 1.5
            if banos > max_banos_logico:
                # Intentar corregir si la diferencia es razonable (puede ser error de dígito)
                if banos <= 10 and recamaras <= 5:  # Solo para casos no extremos
                    # Posible corrección: quitar un dígito (ej: 35 -> 3.5)
                    if banos >= 10 and banos % 10 == 5:
                        nuevo_banos = banos / 10
                        if nuevo_banos <= max_banos_logico:
                            df_corrected.loc[df_corrected.index == idx, 'Banos_totales'] = nuevo_banos
                            changes.append(f'banos_{banos}_a_{nuevo_banos}')
                    # O dividir entre 10 si es muy grande
                    elif banos >= 10:
                        nuevo_banos = banos / 10
                        if nuevo_banos <= max_banos_logico and nuevo_banos >= 1:
                            df_corrected.loc[df_corrected.index == idx, 'Banos_totales'] = nuevo_banos
                            changes.append(f'banos_{banos}_a_{nuevo_banos}')
        
        # 2. Regla de Estacionamientos: estacionamientos <= recámaras + 1
        estacionamientos = row.get('estacionamientos')
        
        if pd.notna(recamaras) and pd.notna(estacionamientos) and recamaras > 0:
            max_estacionamientos_logico = recamaras + 1
            if estacionamientos > max_estacionamientos_logico:
                # Intentar corregir si la diferencia es razonable
                if estacionamientos <= 10 and recamaras <= 5:  # Solo para casos no extremos
                    # Posible corrección: dividir entre 10 si es muy grande
                    if estacionamientos >= 10:
                        nuevo_estacionamientos = estacionamientos / 10
                        if nuevo_estacionamientos <= max_estacionamientos_logico and nuevo_estacionamientos >= 0:
                            df_corrected.loc[df_corrected.index == idx, 'estacionamientos'] = nuevo_estacionamientos
                            changes.append(f'estacionamientos_{estacionamientos}_a_{nuevo_estacionamientos}')
        
        # 3. Corrección de recámaras vacías basada en área (estimación básica)
        area = row.get('area_m2')
        if pd.isna(recamaras) or recamaras <= 0:
            if pd.notna(area) and area > 0:
                # Estimación básica: 1 recámara por cada 45 m², mínimo 1
                recamaras_estimadas = max(1, round(area / 45))
                if recamaras_estimadas <= 4:  # Solo hasta 4 recámaras
                    df_corrected.loc[df_corrected.index == idx, 'recamaras'] = recamaras_estimadas
                    changes.append(f'recamaras_estimadas_{recamaras_estimadas}')
        
        if changes:
            corrected_rows += 1
            corrections_log.append(f"ID {row.get('id', 'unknown')}: {', '.join(changes)}")
    
    print(f"🔧 Correcciones aplicadas a {corrected_rows} propiedades")
    if corrected_rows > 0 and len(corrections_log) <= 10:
        print("📝 Ejemplos de correcciones:")
        for log in corrections_log[:5]:
            print(f"   • {log}")
    
    return df_corrected

def _calculate_physical_coherence(df: pd.DataFrame):
    """Calcula coherencia física usando medidas promedio para departamentos"""
    # Medidas promedio para departamentos
    MEDIDAS_PROMEDIO = {
        'recamara': 9.45,      # m²
        'bano_completo': 3.96,  # m²
        'medio_bano': 1.5,      # m²
        'cocina': 7.5,          # m²
        'sala_estancia': 15.75, # m²
        'estacionamiento': 11.52 # m² (normalmente no cuenta en depto)
    }
    
    coherencia_scores = []
    
    for idx, row in df.iterrows():
        tipo_propiedad = _normalize_property_type(row.get('tipo_propiedad'))
        
        # Solo aplicar a departamentos por ahora
        if tipo_propiedad != 'departamento':
            coherencia_scores.append(np.nan)
            continue
            
        recamaras = row.get('recamaras', 0)
        banos = row.get('Banos_totales', 0)
        area_real = row.get('area_m2', 0)
        
        if pd.isna(recamaras) or pd.isna(banos) or pd.isna(area_real) or area_real <= 0:
            coherencia_scores.append(np.nan)
            continue
        
        # Calcular área esperada
        area_esperada = 0
        
        # Recámaras
        area_esperada += recamaras * MEDIDAS_PROMEDIO['recamara']
        
        # Baños (asumir que .5 = medio baño)
        banos_completos = int(banos)
        medios_banos = 1 if (banos % 1) >= 0.5 else 0
        
        area_esperada += banos_completos * MEDIDAS_PROMEDIO['bano_completo']
        area_esperada += medios_banos * MEDIDAS_PROMEDIO['medio_bano']
        
        # Cocina (1)
        area_esperada += MEDIDAS_PROMEDIO['cocina']
        
        # Sala/Estancia (1)
        area_esperada += MEDIDAS_PROMEDIO['sala_estancia']
        
        # Calcular ratio de coherencia (área_real / área_esperada)
        if area_esperada > 0:
            coherencia = area_real / area_esperada
            coherencia_scores.append(coherencia)
        else:
            coherencia_scores.append(np.nan)
    
    df['coherencia_fisica'] = coherencia_scores
    return df

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
    
    log.info('🔧 Aplicando reglas lógicas de corrección...')
    improved = _apply_logical_rules(improved)
    
    log.info('🏗️ Calculando coherencia física...')
    improved = _calculate_physical_coherence(improved)
    
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
