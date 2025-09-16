"""
ANÁLISIS ESTADÍSTICO PROFESIONAL INMOBILIARIO
=============================================

Sistema especializado para análisis de outliers en propiedades inmobiliarias
Enfocado en las columnas específicas:
- tipo_propiedad (Columna E): Departamentos, Casas, Terrenos, etc.
- area_m2 (Columna F): Superficie de la propiedad
- operacion (Columna I): Venta o Renta
- precio (Columna J): Precio de la propiedad  
- PxM2 (Columna T): Precio por metro cuadrado

Análisis incluido:
✓ Gráficas globales separadas por operación
✓ Estratificación por área, precio y PxM2
✓ Detección profesional de outliers
✓ Gráficas específicas por estratos

Autor: Sistema ESDATA_Epsilon
Fecha: Septiembre 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuración de matplotlib para mejor visualización
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

class AnalizadorInmobiliarioProfesional:
    """Analizador estadístico profesional para datos inmobiliarios"""
    
    def __init__(self, archivo_csv):
        self.archivo = archivo_csv
        self.df = None
        self.df_venta = None
        self.df_renta = None
        
    def cargar_y_preparar_datos(self):
        """Cargar y preparar datos específicos"""
        try:
            print("📂 Cargando datos inmobiliarios...")
            self.df = pd.read_csv(self.archivo)
            
            print(f"✅ Datos cargados: {len(self.df):,} registros")
            print(f"📊 Columnas disponibles: {len(self.df.columns)}")
            
            # Verificar columnas críticas
            columnas_criticas = ['tipo_propiedad', 'area_m2', 'operacion', 'precio', 'PxM2']
            faltantes = [col for col in columnas_criticas if col not in self.df.columns]
            
            if faltantes:
                print(f"❌ Columnas faltantes: {faltantes}")
                return False
            
            # Convertir a numérico donde sea necesario
            for col in ['area_m2', 'precio', 'PxM2']:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Separar por operación
            self.df_venta = self.df[self.df['operacion'] == 'Ven'].copy()
            self.df_renta = self.df[self.df['operacion'] == 'Ren'].copy()
            
            print(f"🏠 DISTRIBUCIÓN POR OPERACIÓN:")
            print(f"   • Ventas: {len(self.df_venta):,} propiedades")
            print(f"   • Rentas: {len(self.df_renta):,} propiedades")
            
            # Mostrar tipos de propiedad
            tipos = self.df['tipo_propiedad'].value_counts()
            print(f"\n🏢 TIPOS DE PROPIEDAD:")
            for tipo, count in tipos.head(8).items():
                print(f"   • {tipo}: {count:,}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def crear_graficas_globales(self):
        """Crear gráficas globales separadas por operación"""
        print("\n📊 CREANDO GRÁFICAS GLOBALES...")
        
        variables = ['precio', 'area_m2', 'PxM2']
        
        for variable in variables:
            self._crear_grafica_global_variable(variable)
    
    def _crear_grafica_global_variable(self, variable):
        """Crear gráfica global para una variable específica"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'📊 ANÁLISIS GLOBAL: {variable.upper()}', fontsize=16, fontweight='bold')
        
        # Datos limpios por operación
        data_venta = self.df_venta[variable].dropna() if self.df_venta is not None else pd.Series()
        data_renta = self.df_renta[variable].dropna() if self.df_renta is not None else pd.Series()
        
        if len(data_venta) == 0 and len(data_renta) == 0:
            print(f"⚠️ No hay datos para {variable}")
            plt.close(fig)
            return
        
        # 1. Histogramas comparativos
        axes[0, 0].hist(data_venta, bins=50, alpha=0.7, color='blue', label=f'Venta ({len(data_venta):,})')
        axes[0, 0].hist(data_renta, bins=50, alpha=0.7, color='red', label=f'Renta ({len(data_renta):,})')
        axes[0, 0].set_title('Distribución por Operación')
        axes[0, 0].set_xlabel(variable)
        axes[0, 0].set_ylabel('Frecuencia')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Box plots comparativos
        data_combined = []
        labels_combined = []
        
        if len(data_venta) > 0:
            data_combined.append(data_venta)
            labels_combined.append('Venta')
        
        if len(data_renta) > 0:
            data_combined.append(data_renta)
            labels_combined.append('Renta')
        
        if data_combined:
            bp = axes[0, 1].boxplot(data_combined, labels=labels_combined, patch_artist=True)
            colors = ['lightblue', 'lightcoral']
            for patch, color in zip(bp['boxes'], colors[:len(data_combined)]):
                patch.set_facecolor(color)
            
            axes[0, 1].set_title('Distribución y Outliers')
            axes[0, 1].set_ylabel(variable)
            axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Detección de outliers - VENTA
        if len(data_venta) > 0:
            Q1_v = data_venta.quantile(0.25)
            Q3_v = data_venta.quantile(0.75)
            IQR_v = Q3_v - Q1_v
            outliers_venta = data_venta[(data_venta < Q1_v - 1.5 * IQR_v) | 
                                      (data_venta > Q3_v + 1.5 * IQR_v)]
            
            # Scatter plot de outliers
            normal_venta = data_venta[~data_venta.isin(outliers_venta)]
            axes[1, 0].scatter(range(len(normal_venta)), normal_venta, 
                             alpha=0.6, color='blue', s=10, label='Normal')
            axes[1, 0].scatter(data_venta.index[data_venta.isin(outliers_venta)], 
                             outliers_venta, color='red', s=30, label='Outliers')
            axes[1, 0].set_title(f'Outliers VENTA: {len(outliers_venta)} de {len(data_venta)} ({len(outliers_venta)/len(data_venta)*100:.1f}%)')
            axes[1, 0].set_xlabel('Índice')
            axes[1, 0].set_ylabel(variable)
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Detección de outliers - RENTA
        if len(data_renta) > 0:
            Q1_r = data_renta.quantile(0.25)
            Q3_r = data_renta.quantile(0.75)
            IQR_r = Q3_r - Q1_r
            outliers_renta = data_renta[(data_renta < Q1_r - 1.5 * IQR_r) | 
                                      (data_renta > Q3_r + 1.5 * IQR_r)]
            
            # Scatter plot de outliers
            normal_renta = data_renta[~data_renta.isin(outliers_renta)]
            axes[1, 1].scatter(range(len(normal_renta)), normal_renta, 
                             alpha=0.6, color='green', s=10, label='Normal')
            axes[1, 1].scatter(data_renta.index[data_renta.isin(outliers_renta)], 
                             outliers_renta, color='orange', s=30, label='Outliers')
            axes[1, 1].set_title(f'Outliers RENTA: {len(outliers_renta)} de {len(data_renta)} ({len(outliers_renta)/len(data_renta)*100:.1f}%)')
            axes[1, 1].set_xlabel('Índice')
            axes[1, 1].set_ylabel(variable)
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'analisis_global_{variable}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Imprimir estadísticas
        self._imprimir_estadisticas_variable(variable, data_venta, data_renta)
    
    def _imprimir_estadisticas_variable(self, variable, data_venta, data_renta):
        """Imprimir estadísticas detalladas de una variable"""
        print(f"\n📈 ESTADÍSTICAS DETALLADAS: {variable.upper()}")
        print("="*60)
        
        if len(data_venta) > 0:
            print(f"🔵 VENTA ({len(data_venta):,} registros):")
            print(f"   • Media: {data_venta.mean():,.2f}")
            print(f"   • Mediana: {data_venta.median():,.2f}")
            print(f"   • Desv. Estándar: {data_venta.std():,.2f}")
            print(f"   • Min: {data_venta.min():,.2f}")
            print(f"   • Max: {data_venta.max():,.2f}")
            
            # Outliers
            Q1 = data_venta.quantile(0.25)
            Q3 = data_venta.quantile(0.75)
            IQR = Q3 - Q1
            outliers = data_venta[(data_venta < Q1 - 1.5 * IQR) | (data_venta > Q3 + 1.5 * IQR)]
            print(f"   • Outliers: {len(outliers)} ({len(outliers)/len(data_venta)*100:.1f}%)")
        
        if len(data_renta) > 0:
            print(f"🔴 RENTA ({len(data_renta):,} registros):")
            print(f"   • Media: {data_renta.mean():,.2f}")
            print(f"   • Mediana: {data_renta.median():,.2f}")
            print(f"   • Desv. Estándar: {data_renta.std():,.2f}")
            print(f"   • Min: {data_renta.min():,.2f}")
            print(f"   • Max: {data_renta.max():,.2f}")
            
            # Outliers
            Q1 = data_renta.quantile(0.25)
            Q3 = data_renta.quantile(0.75)
            IQR = Q3 - Q1
            outliers = data_renta[(data_renta < Q1 - 1.5 * IQR) | (data_renta > Q3 + 1.5 * IQR)]
            print(f"   • Outliers: {len(outliers)} ({len(outliers)/len(data_renta)*100:.1f}%)")
        
        print("="*60)
    
    def crear_analisis_estratificado(self):
        """Crear análisis estratificado por área, precio y PxM2"""
        print("\n🎯 CREANDO ANÁLISIS ESTRATIFICADO...")
        
        # Estratificación por área
        self._analisis_estratificado_area()
        
        # Estratificación por precio
        self._analisis_estratificado_precio()
        
        # Estratificación por PxM2
        self._analisis_estratificado_pxm2()
    
    def _analisis_estratificado_area(self):
        """Análisis estratificado por área"""
        print("\n📐 ESTRATIFICACIÓN POR ÁREA...")
        
        for operacion, df_op in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df_op is None or len(df_op) == 0:
                continue
                
            data_area = df_op[['area_m2', 'precio', 'PxM2']].dropna()
            if len(data_area) == 0:
                continue
            
            # Definir estratos de área
            estratos = [
                (0, 50, 'Muy Pequeña'),
                (50, 100, 'Pequeña'), 
                (100, 200, 'Mediana'),
                (200, 400, 'Grande'),
                (400, float('inf'), 'Muy Grande')
            ]
            
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'📐 ESTRATIFICACIÓN POR ÁREA - {operacion}', fontsize=16, fontweight='bold')
            
            # Análisis por estrato
            estrato_data = []
            for i, (min_area, max_area, nombre) in enumerate(estratos):
                if min_area == 0:
                    mask = data_area['area_m2'] <= max_area
                elif max_area == float('inf'):
                    mask = data_area['area_m2'] > min_area
                else:
                    mask = (data_area['area_m2'] > min_area) & (data_area['area_m2'] <= max_area)
                
                estrato_df = data_area[mask]
                if len(estrato_df) == 0:
                    continue
                
                estrato_data.append({
                    'nombre': nombre,
                    'rango': f'{min_area}-{max_area}' if max_area != float('inf') else f'>{min_area}',
                    'count': len(estrato_df),
                    'precio_mean': estrato_df['precio'].mean(),
                    'precio_median': estrato_df['precio'].median(),
                    'pxm2_mean': estrato_df['PxM2'].mean(),
                    'pxm2_median': estrato_df['PxM2'].median(),
                    'outliers_precio': self._detectar_outliers(estrato_df['precio']),
                    'outliers_pxm2': self._detectar_outliers(estrato_df['PxM2'])
                })
            
            # Crear gráficas por estrato
            if estrato_data:
                # Gráfica 1: Distribución de precios por estrato
                estratos_nombres = [e['nombre'] for e in estrato_data]
                precios_medios = [e['precio_mean'] for e in estrato_data]
                counts = [e['count'] for e in estrato_data]
                
                axes[0, 0].bar(estratos_nombres, precios_medios, color='skyblue')
                axes[0, 0].set_title('Precio Promedio por Estrato')
                axes[0, 0].set_ylabel('Precio Promedio')
                axes[0, 0].tick_params(axis='x', rotation=45)
                
                # Gráfica 2: Cantidad por estrato
                axes[0, 1].bar(estratos_nombres, counts, color='lightgreen')
                axes[0, 1].set_title('Cantidad de Propiedades por Estrato')
                axes[0, 1].set_ylabel('Cantidad')
                axes[0, 1].tick_params(axis='x', rotation=45)
                
                # Gráfica 3: PxM2 promedio por estrato
                pxm2_medios = [e['pxm2_mean'] for e in estrato_data if not np.isnan(e['pxm2_mean'])]
                nombres_pxm2 = [e['nombre'] for e in estrato_data if not np.isnan(e['pxm2_mean'])]
                
                if pxm2_medios:
                    axes[0, 2].bar(nombres_pxm2, pxm2_medios, color='orange')
                    axes[0, 2].set_title('PxM2 Promedio por Estrato')
                    axes[0, 2].set_ylabel('PxM2')
                    axes[0, 2].tick_params(axis='x', rotation=45)
                
                # Gráfica 4: Outliers de precio por estrato
                outliers_precio = [len(e['outliers_precio']) for e in estrato_data]
                axes[1, 0].bar(estratos_nombres, outliers_precio, color='red', alpha=0.7)
                axes[1, 0].set_title('Outliers de Precio por Estrato')
                axes[1, 0].set_ylabel('Cantidad de Outliers')
                axes[1, 0].tick_params(axis='x', rotation=45)
                
                # Gráfica 5: Outliers de PxM2 por estrato
                outliers_pxm2 = [len(e['outliers_pxm2']) for e in estrato_data]
                axes[1, 1].bar(estratos_nombres, outliers_pxm2, color='darkred', alpha=0.7)
                axes[1, 1].set_title('Outliers de PxM2 por Estrato')
                axes[1, 1].set_ylabel('Cantidad de Outliers')
                axes[1, 1].tick_params(axis='x', rotation=45)
                
                # Gráfica 6: Porcentaje de outliers
                pct_outliers = [len(e['outliers_precio'])/e['count']*100 if e['count'] > 0 else 0 for e in estrato_data]
                axes[1, 2].bar(estratos_nombres, pct_outliers, color='purple', alpha=0.7)
                axes[1, 2].set_title('% Outliers de Precio por Estrato')
                axes[1, 2].set_ylabel('Porcentaje (%)')
                axes[1, 2].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'estratos_area_{operacion.lower()}.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            # Imprimir resumen estadístico
            self._imprimir_resumen_estratos('ÁREA', operacion, estrato_data)
    
    def _analisis_estratificado_precio(self):
        """Análisis estratificado por precio"""
        print("\n💰 ESTRATIFICACIÓN POR PRECIO...")
        
        for operacion, df_op in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df_op is None or len(df_op) == 0:
                continue
                
            data_precio = df_op[['precio', 'area_m2', 'PxM2']].dropna()
            if len(data_precio) == 0:
                continue
            
            # Definir estratos de precio basados en percentiles
            if operacion == 'VENTA':
                estratos = [
                    (0, data_precio['precio'].quantile(0.2), 'Económico'),
                    (data_precio['precio'].quantile(0.2), data_precio['precio'].quantile(0.4), 'Accesible'),
                    (data_precio['precio'].quantile(0.4), data_precio['precio'].quantile(0.6), 'Medio'),
                    (data_precio['precio'].quantile(0.6), data_precio['precio'].quantile(0.8), 'Alto'),
                    (data_precio['precio'].quantile(0.8), float('inf'), 'Premium')
                ]
            else:  # RENTA
                estratos = [
                    (0, data_precio['precio'].quantile(0.25), 'Económico'),
                    (data_precio['precio'].quantile(0.25), data_precio['precio'].quantile(0.5), 'Medio'),
                    (data_precio['precio'].quantile(0.5), data_precio['precio'].quantile(0.75), 'Alto'),
                    (data_precio['precio'].quantile(0.75), float('inf'), 'Premium')
                ]
            
            self._crear_graficas_estratos('PRECIO', operacion, data_precio, estratos, 'precio')
    
    def _analisis_estratificado_pxm2(self):
        """Análisis estratificado por PxM2"""
        print("\n📊 ESTRATIFICACIÓN POR PXM2...")
        
        for operacion, df_op in [('VENTA', self.df_venta), ('RENTA', self.df_renta)]:
            if df_op is None or len(df_op) == 0:
                continue
                
            data_pxm2 = df_op[['PxM2', 'area_m2', 'precio']].dropna()
            if len(data_pxm2) == 0:
                continue
            
            # Definir estratos de PxM2 basados en percentiles
            estratos = [
                (0, data_pxm2['PxM2'].quantile(0.2), 'Muy Bajo'),
                (data_pxm2['PxM2'].quantile(0.2), data_pxm2['PxM2'].quantile(0.4), 'Bajo'),
                (data_pxm2['PxM2'].quantile(0.4), data_pxm2['PxM2'].quantile(0.6), 'Medio'),
                (data_pxm2['PxM2'].quantile(0.6), data_pxm2['PxM2'].quantile(0.8), 'Alto'),
                (data_pxm2['PxM2'].quantile(0.8), float('inf'), 'Muy Alto')
            ]
            
            self._crear_graficas_estratos('PXM2', operacion, data_pxm2, estratos, 'PxM2')
    
    def _crear_graficas_estratos(self, tipo, operacion, data, estratos, variable_principal):
        """Crear gráficas para estratos específicos"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'💰 ESTRATIFICACIÓN POR {tipo} - {operacion}', fontsize=16, fontweight='bold')
        
        estrato_data = []
        for min_val, max_val, nombre in estratos:
            if max_val == float('inf'):
                mask = data[variable_principal] > min_val
            else:
                mask = (data[variable_principal] > min_val) & (data[variable_principal] <= max_val)
            
            estrato_df = data[mask]
            if len(estrato_df) == 0:
                continue
            
            outliers_precio = self._detectar_outliers(estrato_df['precio']) if 'precio' in estrato_df.columns else []
            outliers_area = self._detectar_outliers(estrato_df['area_m2']) if 'area_m2' in estrato_df.columns else []
            
            estrato_data.append({
                'nombre': nombre,
                'count': len(estrato_df),
                'precio_mean': estrato_df['precio'].mean() if 'precio' in estrato_df.columns else 0,
                'area_mean': estrato_df['area_m2'].mean() if 'area_m2' in estrato_df.columns else 0,
                'outliers_precio': outliers_precio,
                'outliers_area': outliers_area,
                'data': estrato_df
            })
        
        if not estrato_data:
            plt.close(fig)
            return
        
        # Crear todas las gráficas de estratos
        nombres = [e['nombre'] for e in estrato_data]
        counts = [e['count'] for e in estrato_data]
        precios_mean = [e['precio_mean'] for e in estrato_data]
        areas_mean = [e['area_mean'] for e in estrato_data]
        
        # Distribuciones
        axes[0, 0].bar(nombres, counts, color='lightblue')
        axes[0, 0].set_title(f'Cantidad por Estrato de {tipo}')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        axes[0, 1].bar(nombres, precios_mean, color='lightgreen')
        axes[0, 1].set_title('Precio Promedio por Estrato')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        axes[0, 2].bar(nombres, areas_mean, color='orange')
        axes[0, 2].set_title('Área Promedio por Estrato')
        axes[0, 2].tick_params(axis='x', rotation=45)
        
        # Outliers
        outliers_precio_count = [len(e['outliers_precio']) for e in estrato_data]
        outliers_area_count = [len(e['outliers_area']) for e in estrato_data]
        pct_outliers = [len(e['outliers_precio'])/e['count']*100 if e['count'] > 0 else 0 for e in estrato_data]
        
        axes[1, 0].bar(nombres, outliers_precio_count, color='red', alpha=0.7)
        axes[1, 0].set_title('Outliers de Precio por Estrato')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        axes[1, 1].bar(nombres, outliers_area_count, color='darkred', alpha=0.7)
        axes[1, 1].set_title('Outliers de Área por Estrato')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        axes[1, 2].bar(nombres, pct_outliers, color='purple', alpha=0.7)
        axes[1, 2].set_title('% Outliers por Estrato')
        axes[1, 2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'estratos_{tipo.lower()}_{operacion.lower()}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Imprimir resumen
        self._imprimir_resumen_estratos(tipo, operacion, estrato_data)
    
    def _detectar_outliers(self, series):
        """Detectar outliers usando el método IQR"""
        if len(series) == 0:
            return []
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        outliers = series[(series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)]
        return outliers.tolist()
    
    def _imprimir_resumen_estratos(self, tipo, operacion, estrato_data):
        """Imprimir resumen estadístico de estratos"""
        print(f"\n📈 RESUMEN ESTRATOS {tipo} - {operacion}")
        print("="*70)
        
        for estrato in estrato_data:
            outliers_pct = len(estrato['outliers_precio'])/estrato['count']*100 if estrato['count'] > 0 else 0
            print(f"📊 {estrato['nombre']}:")
            print(f"   • Propiedades: {estrato['count']:,}")
            print(f"   • Precio promedio: ${estrato['precio_mean']:,.0f}")
            print(f"   • Outliers: {len(estrato['outliers_precio'])} ({outliers_pct:.1f}%)")
        
        print("="*70)
    
    def ejecutar_analisis_completo(self):
        """Ejecutar análisis estadístico completo"""
        print("🏠 ANÁLISIS ESTADÍSTICO PROFESIONAL INMOBILIARIO")
        print("="*60)
        
        if not self.cargar_y_preparar_datos():
            return False
        
        # Análisis globales
        self.crear_graficas_globales()
        
        # Análisis estratificados
        self.crear_analisis_estratificado()
        
        print("\n✅ ANÁLISIS ESTADÍSTICO COMPLETADO")
        print("📁 Archivos generados:")
        print("   - analisis_global_precio.png")
        print("   - analisis_global_area_m2.png") 
        print("   - analisis_global_PxM2.png")
        print("   - estratos_area_venta.png / estratos_area_renta.png")
        print("   - estratos_precio_venta.png / estratos_precio_renta.png")
        print("   - estratos_pxm2_venta.png / estratos_pxm2_renta.png")
        
        return True


def main():
    """Función principal"""
    archivo = r"N1_Tratamiento\Consolidados\Sep25\3a.Consolidado_Num_Sep25.csv"
    
    analizador = AnalizadorInmobiliarioProfesional(archivo)
    analizador.ejecutar_analisis_completo()


if __name__ == "__main__":
    main()