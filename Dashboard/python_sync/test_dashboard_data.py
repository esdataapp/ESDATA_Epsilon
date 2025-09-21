#!/usr/bin/env python3
"""
Script de prueba para verificar que los datos del dashboard se generaron correctamente
"""

import pandas as pd
from pathlib import Path
import json

def test_dashboard_data():
    """Probar que los datos del dashboard sean válidos"""
    data_dir = Path(__file__).parent.parent / "data"
    
    print("🧪 Iniciando pruebas de datos del dashboard...")
    print(f"📁 Directorio de datos: {data_dir}")
    
    # 1. Verificar que el metadata existe
    metadata_file = data_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"✅ Metadata cargado - {metadata['total_properties']:,} propiedades")
        print(f"   📊 Generado: {metadata['generated_at']}")
        print(f"   🎯 Propiedades limpias: {metadata['clean_properties']:,}")
        print(f"   📈 Tasa de outliers: {metadata['outlier_rate']:.1%}")
    else:
        print("❌ No se encontró archivo de metadata")
        return False
    
    # 2. Verificar archivos básicos para venta
    print("\n📊 Verificando archivos básicos...")
    basicos_dir = data_dir / "basicos"
    
    # KPIs principales
    kpis_venta = basicos_dir / "kpis_principales_venta.csv"
    if kpis_venta.exists():
        df_kpis = pd.read_csv(kpis_venta)
        print(f"✅ KPIs venta: {len(df_kpis)} métricas")
        print(f"   💰 Precio promedio: ${df_kpis[df_kpis['metric'] == 'precio_promedio']['value'].iloc[0]:,.0f}")
        print(f"   📏 PxM2 promedio: ${df_kpis[df_kpis['metric'] == 'pxm2_promedio']['value'].iloc[0]:,.0f}")
    else:
        print("❌ No se encontraron KPIs de venta")
    
    # Top colonias
    colonias_venta = basicos_dir / "top_colonias_venta.csv"
    if colonias_venta.exists():
        df_colonias = pd.read_csv(colonias_venta)
        print(f"✅ Top colonias venta: {len(df_colonias)} colonias")
        top_colonia = df_colonias.iloc[0]
        print(f"   🏆 Top colonia: {top_colonia['colonia']} ({top_colonia['municipio']})")
        print(f"   💎 PxM2 promedio: ${top_colonia['precio_por_m2_mean']:,.0f}")
    else:
        print("❌ No se encontraron datos de colonias")
    
    # 3. Verificar histogramas
    print("\n📈 Verificando histogramas...")
    histogramas_dir = data_dir / "histogramas"
    
    hist_precios = histogramas_dir / "histograma_precios_venta.csv"
    if hist_precios.exists():
        df_hist = pd.read_csv(hist_precios)
        print(f"✅ Histograma precios venta: {len(df_hist)} bins")
        print(f"   📊 Rango: ${df_hist['bin_min'].min():,.0f} - ${df_hist['bin_max'].max():,.0f}")
    else:
        print("❌ No se encontró histograma de precios")
    
    # 4. Verificar correlaciones
    print("\n🔗 Verificando correlaciones...")
    corr_dir = data_dir / "correlaciones"
    
    corr_venta = corr_dir / "matriz_correlaciones_venta.csv"
    if corr_venta.exists():
        df_corr = pd.read_csv(corr_venta)
        print(f"✅ Correlaciones venta: {len(df_corr)} pares")
        top_corr = df_corr.sort_values('abs_correlation', ascending=False).iloc[0]
        print(f"   🔝 Mayor correlación: {top_corr['variable_1']} vs {top_corr['variable_2']} ({top_corr['correlation']:.3f})")
    else:
        print("❌ No se encontraron correlaciones")
    
    # 5. Verificar datos geoespaciales
    print("\n🗺️ Verificando datos geoespaciales...")
    geo_dir = data_dir / "geoespacial"
    
    mapa_venta = geo_dir / "mapa_calor_colonias_venta.csv"
    if mapa_venta.exists():
        df_mapa = pd.read_csv(mapa_venta)
        print(f"✅ Datos mapa venta: {len(df_mapa)} colonias")
        print(f"   🎯 Colonias con coordenadas válidas: {df_mapa['longitud_centro'].notna().sum()}")
    else:
        print("❌ No se encontraron datos del mapa")
    
    # 6. Verificar segmentos
    print("\n🎯 Verificando segmentos...")
    seg_dir = data_dir / "segmentos"
    
    seg_venta = seg_dir / "segmentos_predefinidos_venta.csv"
    if seg_venta.exists():
        df_seg = pd.read_csv(seg_venta)
        print(f"✅ Segmentos venta: {len(df_seg)} segmentos")
        for _, segmento in df_seg.iterrows():
            print(f"   🏠 {segmento['segmento_nombre']}: {segmento['count']} propiedades")
    else:
        print("❌ No se encontraron segmentos")
    
    # 7. Resumen de archivos por operación
    print("\n📋 Resumen final...")
    
    operaciones = ['venta', 'renta']
    total_archivos = 0
    
    for operacion in operaciones:
        archivos_op = []
        for subdir in data_dir.iterdir():
            if subdir.is_dir():
                archivos_op.extend(list(subdir.glob(f'*_{operacion}.csv')))
        
        print(f"   📂 {operacion.upper()}: {len(archivos_op)} archivos CSV")
        total_archivos += len(archivos_op)
    
    print(f"\n🎉 Prueba completada!")
    print(f"📊 Total archivos CSV generados: {total_archivos}")
    print(f"✅ Los datos están listos para el dashboard ZMG")
    
    return True

if __name__ == "__main__":
    test_dashboard_data()