#!/usr/bin/env python3
"""
Script para generar todos los CSVs necesarios para el Dashboard ZMG
Integración con el pipeline ESDATA_Epsilon existente
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import warnings
from datetime import datetime, timedelta
import sys
import os

warnings.filterwarnings('ignore')

class DashboardDataGenerator:
    def __init__(self, input_num_file, input_ame_file, tablas_dir, output_dir):
        """Inicializar el generador de datos para el dashboard"""
        self.input_num_file = Path(input_num_file)
        self.input_ame_file = Path(input_ame_file)
        self.tablas_dir = Path(tablas_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Crear subdirectorios
        subdirs = ['basicos', 'histogramas', 'segmentos', 'correlaciones', 
                  'amenidades', 'geoespacial', 'series_temporales', 'filtros']
        
        for subdir in subdirs:
            (self.output_dir / subdir).mkdir(exist_ok=True)
        
        # Cargar y combinar datos
        self.cargar_y_combinar_datos()
        
        print(f"✅ Datos cargados: {len(self.df):,} propiedades")
    
    def cargar_y_combinar_datos(self):
        """Cargar los archivos y combinar los datasets"""
        print("📊 Cargando datos numéricos...")
        self.df_num = pd.read_csv(self.input_num_file)
        
        print("📊 Cargando datos de amenidades...")
        self.df_ame = pd.read_csv(self.input_ame_file)
        
        # Combinar los datasets por ID
        print("🔗 Combinando datasets...")
        self.df = pd.merge(
            self.df_num,
            self.df_ame,
            on='id',  # Ambos archivos tienen la columna 'id'
            how='left'
        )
        
        # Mapear columnas al formato estándar
        self.mapear_columnas()
        
        # Limpiar y preparar datos
        self.preparar_datos()
    
    def mapear_columnas(self):
        """Mapear las columnas a nombres estándar para el dashboard"""
        print("🗂️ Mapeando columnas...")
        
        # Mapeo según las columnas reales del archivo Final_Num_Sep25.csv
        column_mapping = {
            'id': 'id_propiedad',
            'PaginaWeb': 'pagina_web',
            'Ciudad': 'ciudad',  # Pero esta parece ser colonia en realidad
            'operacion': 'operacion',
            'tipo_propiedad': 'tipo_propiedad',
            'area_m2': 'superficie_m2',
            'recamaras': 'recamaras',
            'estacionamientos': 'estacionamientos',
            'Banos': 'banos',
            'precio': 'precio',
            'mantenimiento': 'mantenimiento',
            'Colonia': 'colonia_oficial',  # Esta parece estar vacía
            'longitud': 'longitud',
            'latitud': 'latitud',
            'tiempo_publicacion': 'dias_publicacion',
            'Banos_totales': 'banos_totales',
            'antigüedad_icon': 'antiguedad_anos',
            'PxM2': 'precio_por_m2'
        }
        
        # Renombrar solo las columnas que existen
        columns_to_rename = {k: v for k, v in column_mapping.items() if k in self.df.columns}
        self.df = self.df.rename(columns=columns_to_rename)
        
        # Ajuste especial: parece que 'Ciudad' contiene la colonia real
        if 'ciudad' in self.df.columns and 'colonia_oficial' in self.df.columns:
            # Usar 'Ciudad' como colonia si colonia_oficial está vacía
            self.df['colonia'] = self.df['ciudad']
            # Y necesitamos determinar la ciudad real desde el ID o algún otro campo
            self.df['ciudad_real'] = self.df['id_propiedad'].str.split('-').str[0].map({
                'Gdl': 'Guadalajara',
                'Zap': 'Zapopan'
            })
        
        # Crear columna fecha_scrape para análisis temporales (asumir fecha actual para ahora)
        if 'fecha_scrape' not in self.df.columns:
            self.df['fecha_scrape'] = pd.Timestamp.now()
        
        print(f"✅ Columnas mapeadas. Shape final: {self.df.shape}")
    
    def preparar_datos(self):
        """Limpiar y preparar los datos para análisis"""
        print("🧹 Preparando y limpiando datos...")
        
        # Convertir fechas si existen
        if 'fecha_scrape' in self.df.columns:
            self.df['fecha_scrape'] = pd.to_datetime(self.df['fecha_scrape'], errors='coerce')
        
        # Limpiar valores nulos en columnas críticas
        if 'precio' in self.df.columns:
            self.df = self.df.dropna(subset=['precio'])
            # Eliminar precios = 0 o negativos
            self.df = self.df[self.df['precio'] > 0]
        
        # Limpiar superficie
        if 'superficie_m2' in self.df.columns:
            self.df = self.df[self.df['superficie_m2'] > 0]
        
        # Calcular precio por m² si no existe o verificar consistencia
        if 'precio_por_m2' in self.df.columns and 'superficie_m2' in self.df.columns and 'precio' in self.df.columns:
            # Verificar consistencia y recalcular si es necesario
            calculated_pxm2 = self.df['precio'] / self.df['superficie_m2']
            self.df['precio_por_m2'] = calculated_pxm2
        
        # Detectar y eliminar outliers extremos (usando IQR)
        for col in ['precio', 'superficie_m2', 'precio_por_m2']:
            if col in self.df.columns:
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR  # 3 IQR para ser menos restrictivo
                upper_bound = Q3 + 3 * IQR
                
                original_count = len(self.df)
                self.df = self.df[(self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)]
                removed_count = original_count - len(self.df)
                if removed_count > 0:
                    print(f"   Eliminados {removed_count} outliers extremos en {col}")
        
        # Convertir tipos de datos
        numeric_cols = ['precio', 'superficie_m2', 'precio_por_m2', 'recamaras', 'banos', 'estacionamientos']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        print(f"✅ Datos preparados: {len(self.df):,} propiedades válidas")
        
        # Calcular precio por m² si no existe
        if 'precio_por_m2' not in self.df.columns and 'superficie_m2' in self.df.columns:
            self.df['precio_por_m2'] = self.df['precio'] / self.df['superficie_m2']
        
        # Identificar outliers simples
        if 'is_outlier' not in self.df.columns:
            self.df['is_outlier'] = self.identificar_outliers()
        
        # Filtrar outliers para cálculos principales
        self.df_clean = self.df[~self.df['is_outlier']].copy()
        
        print(f"🎯 Datos limpios: {len(self.df_clean):,} propiedades")
    
    def identificar_outliers(self):
        """Identificar outliers usando IQR"""
        outliers = pd.Series(False, index=self.df.index)
        
        for col in ['precio', 'superficie_m2', 'precio_por_m2']:
            if col in self.df.columns:
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers |= (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
        
        return outliers
    
    def generar_todos_los_csvs(self):
        """Generar todos los CSVs necesarios para el dashboard"""
        print("\n🚀 Generando todos los CSVs para el dashboard...")
        
        try:
            # Generar datos para VENTA y RENTA por separado
            operaciones = ['venta', 'renta']
            
            for operacion in operaciones:
                print(f"\n🏷️ Procesando datos para: {operacion.upper()}")
                df_operacion = self.df[self.df['operacion'].str.lower() == operacion].copy()
                
                if len(df_operacion) == 0:
                    print(f"   ⚠️ No hay datos para {operacion}")
                    continue
                
                print(f"   📊 {len(df_operacion):,} propiedades en {operacion}")
                
                # 1. Básicos por operación
                print(f"\n📊 Generando estadísticas básicas para {operacion}...")
                self.generar_kpis_principales(df_operacion, operacion)
                self.generar_top_colonias(df_operacion, operacion)
                self.generar_distribucion_tipos(df_operacion, operacion)
                
                # 2. Histogramas por operación
                print(f"\n📈 Generando histogramas para {operacion}...")
                self.generar_histogramas(df_operacion, operacion)
                
                # 3. Segmentos por operación
                print(f"\n🎯 Generando segmentaciones para {operacion}...")
                self.generar_segmentos(df_operacion, operacion)
                
                # 4. Correlaciones por operación
                print(f"\n🔗 Generando correlaciones para {operacion}...")
                self.generar_correlaciones(df_operacion, operacion)
                
                # 5. Amenidades por operación
                print(f"\n🏠 Analizando amenidades para {operacion}...")
                self.generar_amenidades(df_operacion, operacion)
                
                # 6. Geoespacial por operación
                print(f"\n🗺️ Generando datos geoespaciales para {operacion}...")
                self.generar_datos_mapa(df_operacion, operacion)
                
                # 7. Series temporales por operación
                print(f"\n📅 Generando series temporales para {operacion}...")
                self.generar_series_temporales(df_operacion, operacion)
            
            # 8. Filtros globales (sin separar por operación)
            print("\n🔍 Generando opciones de filtros globales...")
            self.generar_opciones_filtros()
            
            # 9. Metadata global
            self.generar_metadata()
            
            print("\n✅ ¡Todos los CSVs generados exitosamente!")
            self.mostrar_resumen()
            
        except Exception as e:
            print(f"\n❌ Error generando CSVs: {str(e)}")
            raise
    
    def generar_kpis_principales(self, df=None, operacion='all'):
        """Generar KPIs principales para la vista Inicio"""
        if df is None:
            df = self.df_clean
        
        kpis = {
            'metric': [
                'total_propiedades', 'precio_promedio', 'precio_mediana',
                'pxm2_promedio', 'pxm2_mediana', 'superficie_promedio'
            ],
            'value': [
                len(df),
                df['precio'].mean(),
                df['precio'].median(),
                df['precio_por_m2'].mean() if 'precio_por_m2' in df.columns else 0,
                df['precio_por_m2'].median() if 'precio_por_m2' in df.columns else 0,
                df['superficie_m2'].mean() if 'superficie_m2' in df.columns else 0
            ]
        }
        
        kpis_df = pd.DataFrame(kpis)
        filename = f'kpis_principales_{operacion}.csv'
        kpis_df.to_csv(self.output_dir / 'basicos' / filename, index=False)
        print(f"  ✅ KPIs principales {operacion}: {len(kpis_df)} métricas")
    
    def generar_top_colonias(self, df=None, operacion='all'):
        """Generar top colonias por precio por m²"""
        if df is None:
            df = self.df_clean
            
        if 'colonia' not in df.columns:
            print(f"  ⚠️ No hay datos de colonia disponibles para {operacion}")
            return
        
        top_colonias = df.groupby(['colonia', 'municipio']).agg({
            'precio': ['count', 'mean', 'median'],
            'precio_por_m2': ['mean', 'median'] if 'precio_por_m2' in df.columns else ['count']
        }).round(2)
        
        # Aplanar columnas
        top_colonias.columns = ['_'.join(col).strip() for col in top_colonias.columns]
        top_colonias = top_colonias.reset_index()
        
        # Filtrar colonias con al menos 5 propiedades
        top_colonias = top_colonias[top_colonias['precio_count'] >= 5]
        
        # Ordenar por precio por m² promedio
        if 'precio_por_m2_mean' in top_colonias.columns:
            top_colonias = top_colonias.sort_values('precio_por_m2_mean', ascending=False)
        
        top_colonias = top_colonias.head(50)
        
        filename = f'top_colonias_{operacion}.csv'
        top_colonias.to_csv(self.output_dir / 'basicos' / filename, index=False)
        print(f"  ✅ Top colonias {operacion}: {len(top_colonias)} colonias")
    
    def generar_distribucion_tipos(self, df=None, operacion='all'):
        """Generar distribución por tipo de propiedad"""
        if df is None:
            df = self.df_clean
            
        if 'tipo_propiedad' not in df.columns:
            return
        
        distribucion = df.groupby('tipo_propiedad').agg({
            'precio': ['count', 'mean', 'median']
        }).round(2)
        
        distribucion.columns = ['_'.join(col).strip() for col in distribucion.columns]
        distribucion = distribucion.reset_index()
        
        # Calcular porcentajes
        total = distribucion['precio_count'].sum()
        distribucion['percentage'] = (distribucion['precio_count'] / total * 100).round(1)
        
        filename = f'distribucion_tipos_{operacion}.csv'
        distribucion.to_csv(self.output_dir / 'basicos' / filename, index=False)
        print(f"  ✅ Distribución tipos {operacion}: {len(distribucion)} tipos")
    
    def generar_histogramas(self, df=None, operacion='all'):
        """Generar histogramas para filtros dinámicos"""
        if df is None:
            df = self.df_clean
        
        # Histograma de precios
        self._generar_histograma_variable(df, 'precio', 'precios', operacion)
        
        # Histograma de superficie
        if 'superficie_m2' in df.columns:
            self._generar_histograma_variable(df, 'superficie_m2', 'superficie', operacion)
        
        # Histograma de precio por m²
        if 'precio_por_m2' in df.columns:
            self._generar_histograma_variable(df, 'precio_por_m2', 'pxm2', operacion)
    
    def _generar_histograma_variable(self, df, variable, nombre, operacion='all'):
        """Generar histograma para una variable específica"""
        if variable not in df.columns:
            return
        
        data = df[variable].dropna()
        if len(data) == 0:
            return
        
        # Calcular bins usando Freedman-Diaconis
        q75, q25 = np.percentile(data, [75, 25])
        iqr = q75 - q25
        if iqr > 0:
            bin_width = 2 * iqr / (len(data) ** (1/3))
            n_bins = int((data.max() - data.min()) / bin_width)
            n_bins = min(max(n_bins, 10), 50)
        else:
            n_bins = 20
        
        bins, edges = np.histogram(data, bins=n_bins)
        
        histograma_df = pd.DataFrame({
            'bin_min': edges[:-1],
            'bin_max': edges[1:],
            'count': bins,
            'percentage': (bins / len(data)) * 100
        })
        
        filename = f'histograma_{nombre}_{operacion}.csv'
        histograma_df.to_csv(
            self.output_dir / 'histogramas' / filename, 
            index=False
        )
        print(f"  ✅ Histograma {nombre} {operacion}: {len(histograma_df)} bins")
    
    def generar_segmentos(self, df=None, operacion='all'):
        """Generar análisis de segmentaciones predefinidas"""
        if df is None:
            df = self.df_clean
        
        segmentos = {
            'starter_1r_1b': {
                'nombre': 'Starter (1R + 1-1.5B)',
                'filtros': {'recamaras': [1], 'banos': [1, 1.5]}
            },
            'family_2r_2b': {
                'nombre': 'Familiar (2R + 2-2.5B)', 
                'filtros': {'recamaras': [2], 'banos': [2, 2.5]}
            }
        }
        
        resultados_segmentos = []
        
        for seg_id, seg_info in segmentos.items():
            df_segmento = self._aplicar_filtros_segmento(df, seg_info['filtros'])
            
            if len(df_segmento) > 0:
                stats = self._calcular_estadisticas_segmento(df_segmento)
                stats['segmento_id'] = seg_id
                stats['segmento_nombre'] = seg_info['nombre']
                resultados_segmentos.append(stats)
        
        if resultados_segmentos:
            segmentos_df = pd.DataFrame(resultados_segmentos)
            filename = f'segmentos_predefinidos_{operacion}.csv'
            segmentos_df.to_csv(
                self.output_dir / 'segmentos' / filename, 
                index=False
            )
            print(f"  ✅ Segmentos {operacion}: {len(segmentos_df)} segmentos")
    
    def _aplicar_filtros_segmento(self, df, filtros):
        """Aplicar filtros de segmentación"""
        df_filtrado = df.copy()
        
        for campo, valores in filtros.items():
            if campo in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[campo].isin(valores)]
        
        return df_filtrado
    
    def _calcular_estadisticas_segmento(self, df_segmento):
        """Calcular estadísticas para un segmento"""
        stats = {
            'count': len(df_segmento),
            'precio_p25': df_segmento['precio'].quantile(0.25),
            'precio_mediana': df_segmento['precio'].median(),
            'precio_p75': df_segmento['precio'].quantile(0.75)
        }
        
        if 'superficie_m2' in df_segmento.columns:
            stats.update({
                'superficie_mediana': df_segmento['superficie_m2'].median()
            })
        
        return stats
    
    def generar_correlaciones(self, df=None, operacion='all'):
        """Generar matriz de correlaciones"""
        if df is None:
            df = self.df_clean
        
        variables_numericas = []
        candidatas = ['precio', 'superficie_m2', 'precio_por_m2', 'recamaras', 'banos']
        
        for var in candidatas:
            if var in df.columns:
                variables_numericas.append(var)
        
        if len(variables_numericas) < 2:
            return
        
        df_corr = df[variables_numericas].dropna()
        
        if len(df_corr) < 10:
            return
        
        corr_pearson = df_corr.corr(method='pearson')
        
        correlaciones = []
        for i, var1 in enumerate(variables_numericas):
            for j, var2 in enumerate(variables_numericas):
                if i < j:
                    correlaciones.append({
                        'variable_1': var1,
                        'variable_2': var2,
                        'correlation': corr_pearson.loc[var1, var2],
                        'abs_correlation': abs(corr_pearson.loc[var1, var2])
                    })
        
        if correlaciones:
            corr_df = pd.DataFrame(correlaciones)
            filename = f'matriz_correlaciones_{operacion}.csv'
            corr_df.to_csv(
                self.output_dir / 'correlaciones' / filename, 
                index=False
            )
            print(f"  ✅ Correlaciones {operacion}: {len(corr_df)} pares")
    
    def generar_amenidades(self, df=None, operacion='all'):
        """Analizar impacto de amenidades en precio"""
        if df is None:
            df = self.df_clean
        
        if 'amenidades' not in df.columns:
            return
        
        amenidades_comunes = ['piscina', 'gym', 'terraza', 'jardin', 'seguridad']
        
        resultados = []
        
        for amenidad in amenidades_comunes:
            con_amenidad = df[df['amenidades'].str.contains(amenidad, case=False, na=False)]
            sin_amenidad = df[~df['amenidades'].str.contains(amenidad, case=False, na=False)]
            
            if len(con_amenidad) >= 5 and len(sin_amenidad) >= 5:
                precio_con = con_amenidad['precio'].median()
                precio_sin = sin_amenidad['precio'].median()
                lift_porcentaje = ((precio_con - precio_sin) / precio_sin) * 100 if precio_sin > 0 else 0
                
                resultados.append({
                    'amenidad': amenidad,
                    'count_con': len(con_amenidad),
                    'precio_con': precio_con,
                    'precio_sin': precio_sin,
                    'lift_porcentaje': lift_porcentaje
                })
        
        if resultados:
            amenidades_df = pd.DataFrame(resultados)
            filename = f'amenidades_impacto_{operacion}.csv'
            amenidades_df.to_csv(
                self.output_dir / 'amenidades' / filename, 
                index=False
            )
            print(f"  ✅ Amenidades {operacion}: {len(amenidades_df)} analizadas")
    
    def generar_datos_mapa(self, df=None, operacion='all'):
        """Generar datos para el mapa de calor"""
        if df is None:
            df = self.df_clean
        
        if 'colonia' not in df.columns:
            return
        
        mapa_data = df.groupby(['colonia', 'municipio']).agg({
            'precio': ['count', 'median']
        }).reset_index()
        
        mapa_data.columns = ['colonia', 'municipio', 'count', 'precio_mediano']
        mapa_data = mapa_data[mapa_data['count'] >= 3]
        
        filename = f'mapa_calor_colonias_{operacion}.csv'
        mapa_data.to_csv(
            self.output_dir / 'geoespacial' / filename, 
            index=False
        )
        print(f"  ✅ Datos mapa {operacion}: {len(mapa_data)} colonias")
    
    def generar_series_temporales(self, df=None, operacion='all'):
        """Generar series temporales si hay datos de fecha"""
        if df is None:
            df = self.df_clean
        
        if 'fecha_scrape' not in df.columns:
            return
        
        df['year_month'] = df['fecha_scrape'].dt.to_period('M')
        
        series_data = df.groupby('year_month').agg({
            'precio': ['count', 'median']
        }).reset_index()
        
        series_data.columns = ['periodo', 'count', 'precio_mediano']
        
        filename = f'series_zmg_mensual_{operacion}.csv'
        series_data.to_csv(
            self.output_dir / 'series_temporales' / filename, 
            index=False
        )
        print(f"  ✅ Series temporales {operacion}: {len(series_data)} períodos")
    
    def generar_opciones_filtros(self):
        """Generar opciones para filtros del dashboard"""
        df = self.df_clean
        
        # Tipos de propiedad
        if 'tipo_propiedad' in df.columns:
            tipos = df['tipo_propiedad'].value_counts().reset_index()
            tipos.columns = ['tipo', 'count']
            tipos.to_csv(self.output_dir / 'filtros' / 'opciones_tipos.csv', index=False)
        
        # Municipios
        if 'municipio' in df.columns:
            municipios = df['municipio'].value_counts().reset_index()
            municipios.columns = ['municipio', 'count']
            municipios.to_csv(self.output_dir / 'filtros' / 'opciones_municipios.csv', index=False)
        
        print("  ✅ Opciones de filtros generadas")
    
    def generar_metadata(self):
        """Generar metadata del proceso"""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'total_properties': len(self.df),
            'clean_properties': len(self.df_clean),
            'outlier_rate': len(self.df[self.df['is_outlier']]) / len(self.df) if len(self.df) > 0 else 0,
            'columns': list(self.df.columns),
            'data_version': 'v1.0'
        }
        
        with open(self.output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("  ✅ Metadata generada")
    
    def mostrar_resumen(self):
        """Mostrar resumen de archivos generados"""
        print("\n📁 Resumen de archivos generados:")
        
        for subdir in self.output_dir.iterdir():
            if subdir.is_dir():
                archivos = list(subdir.glob('*.csv'))
                if archivos:
                    print(f"  📂 {subdir.name}/: {len(archivos)} archivos")


def main():
    """Función principal"""
    # Configuración de paths
    base_path = Path(__file__).parent.parent.parent
    input_num_file = base_path / "N5_Resultados" / "Nivel_1" / "CSV" / "0.Final_Num_Sep25.csv"
    input_ame_file = base_path / "N5_Resultados" / "Nivel_1" / "CSV" / "0.Final_Ame_Sep25.csv"
    tablas_dir = base_path / "N5_Resultados" / "Nivel_1" / "CSV" / "Tablas" / "Sep25"
    output_dir = base_path / "Dashboard" / "data"
    
    # Verificar que existen los archivos de entrada
    if not input_num_file.exists():
        print(f"❌ No se encontró el archivo numérico: {input_num_file}")
        return
    
    if not input_ame_file.exists():
        print(f"❌ No se encontró el archivo de amenidades: {input_ame_file}")
        return
        
    if not tablas_dir.exists():
        print(f"❌ No se encontró el directorio de tablas: {tablas_dir}")
        return
    
    print(f"📂 Archivo numérico: {input_num_file}")
    print(f"📂 Archivo amenidades: {input_ame_file}")
    print(f"📁 Directorio tablas: {tablas_dir}")
    print(f"📁 Directorio de salida: {output_dir}")
    
    # Crear el generador y ejecutar
    generator = DashboardDataGenerator(input_num_file, input_ame_file, tablas_dir, output_dir)
    generator.generar_todos_los_csvs()
    
    print(f"\n🎉 ¡Proceso completado!")
    print(f"📊 Datos listos para el dashboard en: {output_dir}")


if __name__ == "__main__":
    main()
